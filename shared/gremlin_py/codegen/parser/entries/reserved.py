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
from .errors import ProtoError
from . import lexems as lex

@dataclass
class Reserved:
    """
    Represents a reserved fields declaration in a protobuf message.
    Can contain either field numbers or field names.
    Format:
    ```protobuf
    message Foo {
        reserved 2, 15, 9 to 11;        // reserve field numbers
        reserved "foo", "bar";          // reserve field names
    }
    ```
    """
    start: int
    end: int
    items: List[str] = field(default_factory=list)

    @staticmethod
    def parse(buf: ParserBuffer) -> Optional[Reserved]:
        """
        Attempts to parse a reserved declaration from the given buffer.
        Returns null if the buffer doesn't start with a reserved declaration.

        Parses either field numbers (including ranges) or field names.
        Field numbers and names cannot be mixed in a single declaration.

        :raises ProtoError: If there is a parsing error.
        """
        buf.skip_spaces()
        start = buf.offset

        if not buf.check_str_with_space_and_shift("reserved"):
            return None

        fields = lex.parse_ranges(buf)
        if not fields:
            fields = _parse_field_names(buf)

        buf.semicolon()

        return Reserved(
            start=start,
            end=buf.offset,
            items=fields,
        )

def _parse_field_names(buf: ParserBuffer) -> List[str]:
    """
    Parses a list of field names in quotes.
    Format: "foo", "bar", "baz"

    Returns a list of field names without quotes.
    Returns an empty list if no valid field names are found.
    """
    res = []
    while True:
        buf.skip_spaces()
        name = _parse_field_name(buf)
        if name is None:
            return res

        res.append(name)

        c = buf.char()
        if c == ',':
            buf.offset += 1
        else:
            break
    
    return res

def _parse_field_name(buf: ParserBuffer) -> Optional[str]:
    """
    Parses a single quoted field name.
    Accepts both single and double quotes.
    Returns the field name without quotes, or null if input doesn't start with a quote.
    """
    if buf.char() not in ('"', "'"):
        return None

    snapshot = buf.offset
    try:
        return lex.str_lit(buf)
    except ProtoError:
        buf.offset = snapshot
        return None