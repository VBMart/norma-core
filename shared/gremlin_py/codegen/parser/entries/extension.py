"""
Extensions module provides parsing capabilities for Protocol Buffers v2 extension ranges.
Extensions allow proto2 messages to be extended with new fields outside the normal
numeric range. This module handles parsing the 'extensions' declaration syntax.
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
from typing import List, Optional

from .buffer import ParserBuffer
from . import lexems

class Extensions:
    """
    Extensions represents a proto2 extensions declaration, which defines what field numbers
    are available for extension fields. The declaration can include individual numbers
    and ranges (e.g., "extensions 4, 20 to 30;").
    """

    def __init__(self, start: int, end: int, items: List[str]):
        """
        Initializes an Extensions object.

        :param start: Offset in the source where this extensions declaration begins.
        :param end: Offset in the source where this extensions declaration ends.
        :param items: List of extension ranges, where each item is either a single number
                      or a range in the format "X to Y".
        """
        self.start = start
        self.end = end
        self.items = items

    @staticmethod
    def parse(buf: ParserBuffer) -> Optional[Extensions]:
        """
        Parse an extensions declaration from the given buffer.
        Returns null if the buffer doesn't start with the "extensions" keyword.

        Format examples:
          extensions 4;
          extensions 2, 15, 9 to 11;
        """
        buf.skip_spaces()

        # Remember where this declaration starts
        start = buf.offset

        # Check if this is an extensions declaration
        if not buf.check_str_with_space_and_shift("extensions"):
            return None

        # Parse the comma-separated list of ranges
        fields = lexems.parse_ranges(buf)

        # Expect a semicolon at the end
        buf.semicolon()

        return Extensions(start, buf.offset, fields)

    def contains_field(self, field_number: int) -> bool:
        """
        Returns true if this extensions declaration contains the given field number.
        """
        for item in self.items:
            if " to " in item:
                parts = item.split(" to ")
                try:
                    start = int(parts[0])
                    end = int(parts[1])
                    if start <= field_number <= end:
                        return True
                except (ValueError, IndexError):
                    continue
            else:
                try:
                    num = int(item)
                    if num == field_number:
                        return True
                except ValueError:
                    continue
        return False
