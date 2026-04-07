# Import module provides parsing capabilities for Protocol Buffer import statements.
# This module handles both regular imports and qualified imports (weak/public),
# supporting the full Protocol Buffer import syntax.

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
from enum import Enum
from typing import Optional, TYPE_CHECKING
import os

from .buffer import ParserBuffer
from .lexems import str_lit

if TYPE_CHECKING:
    from .file import ProtoFile

class ImportType(Enum):
    """
    Represents the qualification of an import statement.
    Protocol Buffers supports three types of imports:
    - Regular (no qualifier)
    - Weak (symbols are optional)
    - Public (symbols are re-exported)
    """
    WEAK = "weak"
    PUBLIC = "public"

@dataclass
class Import:
    """
    Represents a single Protocol Buffer import statement.
    Examples:
    ```protobuf
    import "foo/bar.proto";              // Regular import
    import weak "foo/optional.proto";     // Weak import
    import public "foo/reexported.proto"; // Public import
    ```
    """
    start: int
    end: int
    i_type: Optional[ImportType]
    path: str
    target: Optional[ProtoFile] = field(default=None, compare=False)

    @staticmethod
    def parse(buf: ParserBuffer) -> Optional["Import"]:
        """
        Parse an import statement from the given buffer.
        Returns None if the current position doesn't contain an import statement.

        Syntax:
          import [weak|public] "path/to/file.proto";

        Returns:
          Import structure if successful
          None if not an import statement
          Error if invalid syntax
        """
        buf.skip_spaces()
        start = buf.offset

        if not buf.check_str_with_space_and_shift("import"):
            return None

        i_type = None
        if buf.check_str_and_shift("weak"):
            i_type = ImportType.WEAK
        elif buf.check_str_and_shift("public"):
            i_type = ImportType.PUBLIC

        path = str_lit(buf)
        buf.semicolon()

        return Import(
            start=start,
            end=buf.offset,
            i_type=i_type,
            path=path,
        )

    def is_weak(self) -> bool:
        """Returns true if this is a weak import"""
        return self.i_type == ImportType.WEAK

    def is_public(self) -> bool:
        """Returns true if this is a public import"""
        return self.i_type == ImportType.PUBLIC

    def is_resolved(self) -> bool:
        """Returns true if the imported file has been resolved"""
        return self.target is not None

    def basename(self) -> str:
        """Get the basename of the imported file (everything after the last slash)"""
        return os.path.basename(self.path)

    def directory(self) -> str:
        """Get the directory part of the import path (everything before the last slash)"""
        return os.path.dirname(self.path)