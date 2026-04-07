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

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from .buffer import ParserBuffer
from .errors import ProtoError, ParsingError
from . import lexems as lex

@dataclass
class Option:
    """
    Represents a protobuf option declaration.
    Options can appear as standalone declarations or in lists.
    Format:
    option java_package = "com.example.foo";
    message Foo {
        string name = 1 [(custom) = "value", deprecated = true];
    }
    """
    start: int
    end: int
    name: str
    value: str

    def clone(self) -> Option:
        """
        Creates a deep copy of the option.
        """
        return Option(
            start=self.start,
            end=self.end,
            name=self.name,
            value=self.value,
        )

    @staticmethod
    def parse(buf: ParserBuffer) -> Optional[Option]:
        """
        Attempts to parse a standalone option declaration from the given buffer.
        Returns null if the buffer doesn't start with an option declaration.
        """
        buf.skip_spaces()
        start = buf.offset

        if not buf.check_str_with_space_and_shift("option"):
            return None

        name = _option_name(buf)
        buf.assignment()
        value = lex.constant(buf)

        buf.semicolon()

        return Option(
            start=start,
            end=buf.offset,
            name=name,
            value=value,
        )

    @staticmethod
    def parse_list(buf: ParserBuffer) -> Optional[List[Option]]:
        """
        Attempts to parse a list of options enclosed in square brackets.
        Format: [option1 = value1, option2 = value2]
        Returns null if the buffer doesn't start with '['
        """
        buf.skip_spaces()
        if buf.char() != '[':
            return None
        buf.offset += 1
        buf.skip_spaces()

        if buf.char() == ']':
            buf.offset += 1
            return []

        res = []
        while True:
            start = buf.offset
            name = _option_name(buf)
            buf.assignment()
            value = lex.constant(buf)

            res.append(Option(
                start=start,
                end=buf.offset,
                name=name,
                value=value,
            ))

            buf.skip_spaces()
            c = buf.char()
            if c is None:
                raise ProtoError(ParsingError.UnexpectedEOF)

            if c == ',':
                buf.offset += 1
                continue
            elif c == ']':
                buf.offset += 1
                return res
            else:
                raise ProtoError(ParsingError.InvalidCharacter)

def _option_name(buf: ParserBuffer) -> str:
    """
    Parses a complete option name, which can include multiple parts
    separated by dots and custom scopes in parentheses.
    Format: part1.part2.(custom.scope).part3
    """
    buf.skip_spaces()
    start = buf.offset
    while True:
        _option_name_part(buf)
        if buf.char() != '.':
            break
        buf.offset += 1

    return buf.buf[start:buf.offset]

def _option_name_part(buf: ParserBuffer):
    """
    Parses a single part of an option name.
    Can be either a simple identifier or a custom scope in parentheses.
    """
    c = buf.char()
    if c is None:
        raise ProtoError(ParsingError.InvalidOptionName)

    if c == '(':
        buf.offset += 1
        if buf.char() == '.':
            buf.offset += 1
        _ = lex.full_ident(buf)
        if not buf.check_and_shift(')'):
            raise ProtoError(ParsingError.InvalidOptionName)
    else:
        _ = lex.ident(buf)