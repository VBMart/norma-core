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
from .buffer import ParserBuffer
from .scoped_name import ScopedName
from .lexems import full_scoped_name
from typing import Optional

class Package:
    """
    Represents a package declaration in a protobuf file.
    The package name specifies the namespace for message types.
    Format:
    ```protobuf
    package foo.bar.baz;
    ```
    """

    def __init__(self, start: int, end: int, name: ScopedName):
        self.start = start
        self.end = end
        self.name = name

    @classmethod
    def parse(cls, buf: ParserBuffer) -> Optional[Package]:
        """
        Attempts to parse a package declaration from the given buffer.
        Returns None if the buffer doesn't start with a package declaration.

        The package name must be a dot-separated sequence of identifiers.
        The declaration must end with a semicolon.

        :raises ProtoError: If there is a parsing error.
        """
        buf.skip_spaces()

        start = buf.offset

        if not buf.check_str_with_space_and_shift("package"):
            return None

        name = full_scoped_name(buf)
        
        buf.semicolon()

        return Package(
            start=start,
            name=name,
            end=buf.offset,
        )
