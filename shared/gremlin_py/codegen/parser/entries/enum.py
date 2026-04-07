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
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from .buffer import ParserBuffer
from .errors import ProtoError, ParsingError
from . import lexems as lex
from .option import Option
from .reserved import Reserved
from .scoped_name import ScopedName

if TYPE_CHECKING:
    from .message import Message

@dataclass
class EnumField:
    """
    Represents a single field within an enum declaration.
    Example: FOO = 1 [deprecated = true];
    """
    start: int
    end: int
    name: str
    index: int
    options: Optional[List[Option]] = None

    @staticmethod
    def parse(buf: ParserBuffer) -> Optional[EnumField]:
        """
        Parse an enum field from the buffer.
        Returns null if the current buffer position doesn't contain an enum field.

        Format:
          FIELD_NAME = NUMBER [options];
        """
        snapshot = buf.offset
        try:
            buf.skip_spaces()
            start = buf.offset

            name = lex.ident(buf)
            buf.assignment()
            value_str = lex.int_lit(buf)

            parsed_value: int
            try:
                if 'x' in value_str.lower():
                    parsed_value = int(value_str, 16)
                elif value_str.startswith('0') and len(value_str) > 1:
                    parsed_value = int(value_str, 8)
                elif value_str.startswith('-0') and len(value_str) > 2:
                    parsed_value = int(value_str, 8)
                else:
                    parsed_value = int(value_str, 10)
            except ValueError:
                raise ProtoError(ParsingError.InvalidIntegerLiteral)

            opts = Option.parse_list(buf)
            buf.semicolon()

            return EnumField(
                start=start,
                end=buf.offset,
                name=name,
                index=parsed_value,
                options=opts,
            )
        except ProtoError:
            buf.offset = snapshot
            return None

@dataclass
class Enum:
    """
    Represents a complete Protocol Buffer enum declaration, including
    its name, fields, options, and reserved ranges.
    """
    start: int
    end: int
    name: ScopedName
    options: List[Option] = field(default_factory=list)
    fields: List[EnumField] = field(default_factory=list)
    reserved: List[Reserved] = field(default_factory=list)
    parent: Optional['Message'] = None

    @staticmethod
    def parse(buf: ParserBuffer, parent: Optional[ScopedName]) -> Optional[Enum]:
        """
        Parse an enum declaration from the buffer.
        Returns null if the current buffer position doesn't start with "enum".

        Format:
          enum EnumName {
            option opt = "value";  // enum options
            UNKNOWN = 0;           // enum fields
            reserved 1, 2;         // reserved numbers
          }
        """
        buf.skip_spaces()
        offset = buf.offset

        if not buf.check_str_with_space_and_shift("enum"):
            return None

        name = lex.ident(buf)
        buf.open_bracket()

        opts: List[Option] = []
        fields: List[EnumField] = []
        reserved: List[Reserved] = []

        while True:
            buf.skip_spaces()

            if buf.char() == '}':
                buf.offset += 1
                break

            if buf.char() == ';':
                buf.offset += 1
                continue

            opt = Option.parse(buf)
            if opt is not None:
                opts.append(opt)
                continue

            res = Reserved.parse(buf)
            if res is not None:
                reserved.append(res)
                continue

            field_ = EnumField.parse(buf)
            if field_ is not None:
                fields.append(field_)
                continue
            
            raise ProtoError(ParsingError.InvalidCharacter)

        scoped_name = parent.child(name) if parent else ScopedName(name)

        return Enum(
            start=offset,
            end=buf.offset,
            name=scoped_name,
            options=opts,
            fields=fields,
            reserved=reserved,
        )

    def find_field(self, name: str) -> Optional[EnumField]:
        """Find a field by name"""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def find_field_by_value(self, value: int) -> Optional[EnumField]:
        """Find a field by value"""
        for f in self.fields:
            if f.index == value:
                return f
        return None