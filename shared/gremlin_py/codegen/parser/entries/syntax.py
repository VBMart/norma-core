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
from .errors import ParsingError,ProtoError

VALID_VERSIONS = [
    "'proto3'",
    '"proto3"',
    "'proto2'",
    '"proto2"',
]

@dataclass
class Syntax:
    """
    Represents a syntax declaration in a protobuf file.
    Format: syntax = "proto2"|"proto3";
    """
    start: int
    end: int

    @classmethod
    def parse(cls, buf: ParserBuffer) -> Syntax | None:
        """
        Attempts to parse a syntax declaration from the given buffer.
        Returns None if the buffer doesn't start with a syntax declaration.
        Raises ParsingError if the syntax declaration is malformed.

        Expected format:
        ```protobuf
        syntax = "proto3";
        ```

        :param buf: The parser buffer.
        :return: A Syntax object or None.
        :raises ParsingError: If there is a parsing error.
        """
        offset = buf.offset
        if not buf.check_str_and_shift("syntax"):
            return None
        
        buf.assignment()

        for version in VALID_VERSIONS:
            if buf.check_str_and_shift(version):
                buf.semicolon()
                return Syntax(start=offset, end=buf.offset)
        
        raise ProtoError(ParsingError.InvalidSyntaxVersion)
