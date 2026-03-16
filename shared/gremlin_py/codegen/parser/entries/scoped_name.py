"""
Scoped name handling module for Protocol Buffer definitions.
Provides utilities for parsing and manipulating fully qualified names
in Protocol Buffer definitions (e.g., "package.Message.SubMessage").
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
import copy
from typing import List, Optional, Union

class ScopedName:
    """
    Represents a fully qualified name in Protocol Buffer definitions.
    Handles parsing and manipulation of names like "foo.bar.Baz".
    """

    name: str
    parent: Optional[List[str]]
    full: str

    def __init__(self, src: Union[str, ScopedName]):
        """
        Creates a new ScopedName from a string or another ScopedName.
        Handles both simple names ("Message") and qualified names ("pkg.Message").
        """
        if isinstance(src, ScopedName):
            self.full = src.full
            self.name = src.name
            self.parent = copy.copy(src.parent) if src.parent is not None else None
            return

        self.full = src
        parts = src.split('.')
        self.name = parts[-1]
        if len(parts) > 1:
            self.parent = parts[:-1]
        else:
            self.parent = None

    def clone(self) -> ScopedName:
        """Creates a deep copy of the ScopedName."""
        return ScopedName(self)

    def child(self, name: str) -> ScopedName:
        """
        Creates a new ScopedName representing a child of this name.
        For example: "foo.bar".child("baz") -> "foo.bar.baz"
        """
        if self.full == ".":
            return ScopedName(f".{name}")
        return ScopedName(f"{self.full}.{name}")

    @property
    def get_parent(self) -> Optional[ScopedName]:
        """
        Gets the parent scope of this name.
        For example: "foo.bar.baz".get_parent -> "foo.bar"
        """
        if self.full == '.':
            return None
        if self.parent is None:
            return None

        parent_full = ".".join(self.parent)
        
        if not parent_full and self.full.startswith('.'):
            return ScopedName('.')

        if not parent_full:
            return None

        return ScopedName(parent_full)

    def __eq__(self, other: object) -> bool:
        """
        Checks if two scoped names are equivalent.
        Handles both absolute paths (starting with dot) and relative paths.
        """
        if not isinstance(other, ScopedName):
            return NotImplemented

        if self.full == other.full:
            return True
        if self.full.startswith('.') and other.full.startswith('.'):
            return False

        if self.full.startswith('.') and self.full[1:] == other.full:
            return True
        if other.full.startswith('.') and self.full == other.full[1:]:
            return True
        return False

    def to_scope(self, target: ScopedName) -> ScopedName:
        """
        Resolves this name relative to a target scope.
        For example: "Message".to_scope(ScopedName("pkg.sub")) -> "pkg.sub.Message"
        """
        if self.full.startswith('.'):
            return self.clone()

        if target.full == ".":
            return ScopedName(f".{self.full}")
        return ScopedName(f"{target.full}.{self.full}")


    def __str__(self) -> str:
        return self.full

    def __repr__(self) -> str:
        return f"ScopedName('{self.full}')"