"""
Extend declaration parser module for Protocol Buffer text format.
Handles parsing of extend blocks and their fields, which allow extending
existing message types with additional fields.
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

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .buffer import ParserBuffer
from . import lexems as lex
from .option import Option
from .scoped_name import ScopedName

@dataclass
class ExtendField:
    """
    Represents a single field within an extend block.
    Each field has a type, name, number, and optional modifiers/options.
    """
    start: int
    end: int
    f_name: str
    f_type: str
    f_value: str
    optional: bool
    repeated: bool
    options: Optional[List[Option]] = None

    @staticmethod
    def parse(buf: ParserBuffer) -> Optional[ExtendField]:
        """
        Parses a single extend field declaration.
        Format: [optional|repeated] type name = number [options];
        """
        buf.skip_spaces()
        start = buf.offset

        optional = buf.check_str_and_shift("optional")
        if optional:
            buf.skip_spaces()

        repeated = buf.check_str_and_shift("repeated")
        if repeated:
            buf.skip_spaces()

        f_type = lex.field_type(buf)
        name = lex.ident(buf)
        buf.assignment()
        value = lex.int_lit(buf)
        opts = Option.parse_list(buf)
        buf.semicolon()

        return ExtendField(
            start=start,
            end=buf.offset,
            optional=optional,
            repeated=repeated,
            f_name=name,
            f_type=f_type,
            f_value=value,
            options=opts,
        )

@dataclass
class Extend:
    """
    Represents a complete extend block declaration which extends
    an existing message type with new fields.
    """
    start: int
    end: int
    base: ScopedName
    fields: List[ExtendField] = field(default_factory=list)

    @staticmethod
    def parse(buf: ParserBuffer) -> Optional[Extend]:
        """
        Parses a complete extend block.
        Format: extend MessageType { fields... }
        """
        buf.skip_spaces()
        offset = buf.offset
        if not buf.check_str_with_space_and_shift("extend"):
            return None

        base_src = lex.field_type(buf)
        base = ScopedName(base_src)
        buf.open_bracket()

        fields = []
        
        c = buf.char()
        if c == '}':
            buf.offset += 1
        else:
            while True:
                field_obj = ExtendField.parse(buf)
                if field_obj:
                    fields.append(field_obj)
                
                buf.skip_spaces()
                ec = buf.char()
                if ec == ';':
                    buf.offset += 1
                elif ec == '}':
                    buf.offset += 1
                    break
        
        return Extend(
            start=offset,
            end=buf.offset,
            base=base,
            fields=fields,
        )