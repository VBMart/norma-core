"""
Group parser module for Protocol Buffer definitions.
Handles parsing of the deprecated 'group' syntax in proto2.
Groups were replaced by nested messages in proto3, but must still be
parsed for backwards compatibility with proto2 files.
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
from dataclasses import dataclass
from typing import Optional

from .buffer import ParserBuffer
from . import lexems as lex

@dataclass
class Group:
    """
    Represents a proto2 group definition.
    Groups are a deprecated way to define nested message types.
    Format: [optional|required|repeated] group GroupName = number { ... }
    """
    start: int
    end: int

    @staticmethod
    def parse(buf: ParserBuffer) -> Optional[Group]:
        """
        Attempts to parse a group definition from the buffer.
        Returns None if the input does not start with a group.

        # Protocol Buffer Group Syntax
        ```proto
        [optional|required|repeated] group GroupName = number {
          // fields...
        }
        ```

        # Errors
        Raises ProtoError on invalid syntax or buffer overflow.
        """
        offset = buf.offset
        buf.skip_spaces()

        # Parse optional modifiers (optional, required, repeated)
        _ = buf.check_str_with_space_and_shift("optional")
        buf.skip_spaces()
        _ = buf.check_str_with_space_and_shift("required")
        buf.skip_spaces()
        _ = buf.check_str_with_space_and_shift("repeated")
        buf.skip_spaces()

        # Check if this is actually a group
        if not buf.check_str_with_space_and_shift("group"):
            buf.offset = offset
            return None

        # Parse group name and number
        _ = lex.ident(buf)
        buf.assignment()
        _ = lex.int_lit(buf)

        # Skip the group body by counting braces
        brace_depth = 0
        while True:
            c = buf.should_shift_next()
            if c == '{':
                brace_depth += 1
            elif c == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    break
        
        return Group(start=offset, end=buf.offset)