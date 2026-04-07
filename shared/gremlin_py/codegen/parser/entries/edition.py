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
from .buffer import ParserBuffer
from . import lexems

@dataclass
class Edition:
    """
    Represents a parsed edition declaration from Protocol Buffer text format.
    Tracks the source positions for error reporting and stores the edition value.
    """
    start: int
    end: int
    edition: str

    @classmethod
    def parse(cls, buf: ParserBuffer) -> Edition | None:
        """
        Attempts to parse an edition declaration from the given buffer.
        Returns null if no edition declaration is found at the current position.

        Format: edition = "2018";

        # Errors
        Returns an error if:
        - The assignment operator (=) is missing or malformed
        - The edition string is not a valid string literal
        - The semicolon is missing
        """
        buf.skip_spaces()
        offset = buf.offset

        if not buf.check_str_and_shift("edition"):
            return None

        buf.assignment()
        edition_value = lexems.str_lit(buf)
        buf.semicolon()

        return Edition(
            start=offset,
            end=buf.offset,
            edition=edition_value,
        )