"""
A lexical analyzer for Protocol Buffers (protobuf) file format.
This module handles parsing of various protobuf literals, identifiers,
and field types according to the protobuf specification.
"""

#               .'\   /`.
#             .'.-.`-'.-.`.
#        ..._:   .-. .-.   :_...
#      .'    '-.(o ) (o ).-'    `.
#     :  _    _ _`~(_)~`_ _    _  :
#    :  /:   ' .-=_   _=-. `   ;\  :
#    :   :|-.._  '     `  _..-|:   :
#     :   `:| |`:-:-.-:-:'| |:'   :
#      `.   `.| | | | | | |.'   .'
#        `.   `-:_| | |_:-'   .'
#          `-._   ````    _.-'
#              ``-------''
#
# Created by ab, 24.11.2025

import string
from .errors import ParsingError, ProtoError
from .buffer import ParserBuffer
from .scoped_name import ScopedName
from typing import List, Optional

def _is_octal_digit(c: str) -> bool:
    """Checks if a character is an octal digit."""
    return '0' <= c <= '7'

def _parse_unicode_escape(buf: ParserBuffer, count: int):
    """Parses a Unicode escape sequence of a given length."""
    for _ in range(count):
        char = buf.should_shift_next()
        if char is None or char.lower() not in string.hexdigits:
            raise ProtoError(ParsingError.InvalidUnicodeEscape)

def _parse_extended_unicode_escape(buf: ParserBuffer):
    """Parses an extended Unicode escape sequence."""
    if not buf.check_and_shift('0') or not buf.check_and_shift('0'):
        raise ProtoError(ParsingError.InvalidUnicodeEscape)

    next_char = buf.should_shift_next()
    if next_char == '0':
        _parse_unicode_escape(buf, 5)
    elif next_char == '1':
        if not buf.check_and_shift('0'):
            raise ProtoError(ParsingError.InvalidUnicodeEscape)
        _parse_unicode_escape(buf, 4)
    else:
        raise ProtoError(ParsingError.InvalidUnicodeEscape)

def _parse_escape_sequence(buf: ParserBuffer):
    """Parses an escape sequence within a string literal."""
    next_char = buf.should_shift_next()
    if next_char is None:
        raise ProtoError(ParsingError.UnexpectedEOF)
        
    if next_char.lower() == 'x':
        if buf.char() is None or buf.char().lower() not in string.hexdigits:
             raise ProtoError(ParsingError.InvalidEscape)
        while buf.char() is not None and buf.char().lower() in string.hexdigits:
            buf.offset += 1
    elif '0' <= next_char <= '7':
        while buf.char() is not None and _is_octal_digit(buf.char()):
            buf.offset += 1
    elif next_char in ('a', 'b', 'f', 'n', 'r', 't', 'v', '\\', '\'', '"', '?'):
        pass
    elif next_char == 'u':
        _parse_unicode_escape(buf, 4)
    elif next_char == 'U':
        _parse_extended_unicode_escape(buf)
    else:
        raise ProtoError(ParsingError.InvalidEscape)

def _str_lit_single(buf: ParserBuffer, close: str):
    """Helper to parse the content of a string literal until the closing quote."""
    while True:
        c = buf.should_shift_next()
        if c == close:
            return

        if c == '\\':
            _parse_escape_sequence(buf)
        elif c == '\0' or c == '\n':
            raise ProtoError(ParsingError.InvalidStringLiteral)

def str_lit(buf: ParserBuffer) -> str:
    """Parse a string literal. Handles both single and double quotes."""
    buf.skip_spaces()
    start_offset = buf.offset
    open_char = buf.should_shift_next()
    if open_char not in ('"', "'"):
        raise ProtoError(ParsingError.InvalidStringLiteral)
    
    _str_lit_single(buf, open_char)
    end_offset = buf.offset

    return buf.buf[(start_offset + 1):(end_offset - 1)]

def _is_identifier_char(c: str) -> bool:
    """Checks if a character is valid for an identifier."""
    return c.isalnum() or c == '_'

def ident(buf: ParserBuffer) -> str:
    """Parse a simple identifier."""
    buf.skip_spaces()
    start_offset = buf.offset
    c = buf.should_shift_next()
    if c != '_' and not c.isalpha():
        raise ProtoError(ParsingError.IdentifierShouldStartWithLetter)

    while True:
        n = buf.char()
        if n is None or not _is_identifier_char(n):
            break
        buf.offset += 1

    return buf.buf[start_offset:buf.offset]

def full_ident(buf: ParserBuffer) -> str:
    """Parse a full identifier (including dots)."""
    buf.skip_spaces()
    start_offset = buf.offset

    # First part is mandatory
    _ = ident(buf)

    while True:
        if buf.char() != '.':
            break

        # Look ahead. If an ident doesn't follow the dot, break.
        snapshot = buf.offset
        buf.offset += 1  # Tentatively consume dot
        try:
            _ = ident(buf)
            # It succeeded. The buffer is now past the next ident. Continue loop.
        except ProtoError as e:
            # If it failed because of an invalid char, it's a real error.
            if e.error_code == ParsingError.IdentifierShouldStartWithLetter:
                raise  # Propagate the error

            # Otherwise, it was probably just EOF or a delimiter.
            # So we backtrack and break.
            buf.offset = snapshot
            break

    return buf.buf[start_offset:buf.offset]

def full_scoped_name(buf: ParserBuffer) -> ScopedName:
    """Parse a fully scoped name."""
    name = full_ident(buf)
    if name.startswith("."):
        return ScopedName(name)
    else:
        return ScopedName(f".{name}")

def _parse_decimal_digits(buf: ParserBuffer):
    """Parses a sequence of decimal digits."""
    while True:
        n = buf.char()
        if n is None or not n.isdigit():
            break
        buf.offset += 1

def _parse_octal_or_hex(buf: ParserBuffer):
    """Parses an octal or hexadecimal number."""
    x = buf.char()
    if x is None:
        return
        
    if x.lower() == 'x':
        buf.offset += 1
        if buf.char() is None or buf.char().lower() not in string.hexdigits:
            raise ProtoError(ParsingError.InvalidIntegerLiteral)
        while True:
            n = buf.char()
            if n is None or n.lower() not in string.hexdigits:
                break
            buf.offset += 1
    else:
        while True:
            n = buf.char()
            if n is None or not _is_octal_digit(n):
                break
            buf.offset += 1

def int_lit(buf: ParserBuffer) -> str:
    """Parse an integer literal."""
    buf.skip_spaces()
    start = buf.offset

    if buf.char() == '-':
        buf.offset += 1
        buf.skip_spaces()

    c = buf.should_shift_next()
    if '1' <= c <= '9':
        _parse_decimal_digits(buf)
    elif c == '0':
        _parse_octal_or_hex(buf)
    else:
        raise ProtoError(ParsingError.InvalidIntegerLiteral)

    return buf.buf[start:buf.offset]

def _decimals(buf: ParserBuffer):
    """Helper to parse decimal parts of a float."""
    _parse_decimal_digits(buf)

def _exponent(buf: ParserBuffer):
    """Helper to parse the exponent part of a float."""
    c = buf.char()
    if c is None or c.lower() != 'e':
        return

    buf.offset += 1
    buf.skip_spaces()

    sign = buf.char()
    if sign in ('+', '-'):
        buf.offset += 1
        buf.skip_spaces()

    _decimals(buf)

def float_lit(buf: ParserBuffer) -> str:
    """Parse a floating-point literal."""
    buf.skip_spaces()
    start = buf.offset

    if buf.char() == '-':
        buf.offset += 1
    
    buf.skip_spaces()

    if buf.check_str_and_shift("inf"):
        return buf.buf[start:buf.offset]
    if buf.check_str_and_shift("nan"):
        return buf.buf[start:buf.offset]

    initial_offset = buf.offset
    
    c = buf.char()
    if c == '.':
        buf.offset += 1
        _decimals(buf)
        _exponent(buf)
    else:
        _decimals(buf)
        if buf.offset == initial_offset: # No digits consumed
             raise ProtoError(ParsingError.InvalidFloat)
        next_c = buf.char()
        if next_c == '.':
            buf.offset += 1
            _decimals(buf)
            _exponent(buf)
        else:
            _exponent(buf)
    
    if buf.offset == initial_offset and not (buf.check_str_and_shift("inf") or buf.check_str_and_shift("nan")):
        raise ProtoError(ParsingError.InvalidFloat)

    return buf.buf[start:buf.offset]

def bool_lit(buf: ParserBuffer) -> str:
    """Parse a boolean literal."""
    buf.skip_spaces()
    start = buf.offset

    if buf.check_str_and_shift("true"):
        return buf.buf[start:buf.offset]
    if buf.check_str_and_shift("false"):
        return buf.buf[start:buf.offset]

    raise ProtoError(ParsingError.InvalidBooleanLiteral)

def constant(buf: ParserBuffer) -> str:
    """Parse a constant value."""
    buf.skip_spaces()
    start_offset = buf.offset
    
    # Each parsing function is attempted; if it fails, the buffer is reset.
    # The result is returned only if the whole token is consumed.

    for parser in [float_lit, int_lit, full_ident]:
        try:
            res = parser(buf)
            # After parsing, if the buffer is not at its end,
            # and the next character is not a delimiter, then it's not a full match.
            if buf.offset < len(buf.buf) and buf.char() not in (' ', '\t', '\n', '\r', ';', '}', ']', ','):
                buf.offset = start_offset
                continue
            return res
        except ProtoError:
            buf.offset = start_offset

    # Handle str_lit separately to include quotes in the result
    try:
        _ = str_lit(buf)  # This advances the buffer
        res = buf.buf[start_offset:buf.offset]
        if buf.offset < len(buf.buf) and buf.char() not in (' ', '\t', '\n', '\r', ';', '}', ']', ','):
            buf.offset = start_offset
            # This will be caught and we'll raise InvalidConst at the end
            raise ProtoError(ParsingError.InvalidConst)
        return res
    except ProtoError:
        buf.offset = start_offset


    raise ProtoError(ParsingError.InvalidConst)

BASE_TYPES = [
    "double", "float", "int32", "int64", "uint32", "uint64",
    "sint32", "sint64", "fixed32", "fixed64", "sfixed32",
    "sfixed64", "bool", "string", "bytes"
]

def field_type(buf: ParserBuffer) -> str:
    """Parse a field type (base type or message type)."""
    buf.skip_spaces()

    for base_type in BASE_TYPES:
        if buf.check_str_with_space_and_shift(base_type):
            return base_type

    return message_type(buf)

def message_type(buf: ParserBuffer) -> str:
    """Parse a message type (a fully qualified identifier)."""
    start = buf.offset
    c = buf.char()
    if c == '.':
        buf.offset += 1

    while True:
        initial_offset = buf.offset
        try:
            part = ident(buf)
            if not part:
                buf.offset = initial_offset
                break
        except ProtoError:
            buf.offset = initial_offset
            break
        
        iter_c = buf.char()
        if iter_c != '.':
            break
        buf.offset += 1

    return buf.buf[start:buf.offset]

def parse_range(buf: ParserBuffer) -> Optional[str]:
    """Parse a single range in a 'ranges' definition."""
    buf.skip_spaces()
    snapshot = buf.offset
    
    try:
        int_lit(buf)
    except ProtoError:
        buf.offset = snapshot
        return None
        
    buf.skip_spaces()
    if buf.check_str_with_space_and_shift("to"):
        buf.skip_spaces()
        if not buf.check_str_and_shift("max"):
            snapshot2 = buf.offset
            try:
                int_lit(buf)
            except ProtoError:
                buf.offset = snapshot2

    return buf.buf[snapshot:buf.offset]

def parse_ranges(buf: ParserBuffer) -> List[str]:
    """Parse ranges in the format "2", "15", "9 to 11"."""
    res = []
    while True:
        buf.skip_spaces()
        range_str = parse_range(buf)
        if not range_str:
            return res
        
        res.append(range_str.strip())

        c = buf.char()
        if c == ',':
            buf.offset += 1
        else:
            break
    
    return res