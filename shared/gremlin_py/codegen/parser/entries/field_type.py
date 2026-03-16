"""
Field type parser module for Protocol Buffer definitions.
Handles parsing and validation of field types including scalar types,
bytes/string types, and message/enum references.
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
from typing import Optional, TYPE_CHECKING

from .buffer import ParserBuffer
from . import lexems as lex
from .scoped_name import ScopedName
if TYPE_CHECKING:
    from .enum import Enum
    from .message import Message
    from .file import ProtoFile

SCALAR_TYPES = [
    "bool", "float", "double", "int32", "int64", "uint32", "uint64",
    "sint32", "sint64", "fixed32", "fixed64", "sfixed32", "sfixed64"
]

def is_scalar_type(src: str) -> bool:
    """Checks if a type name is a Protocol Buffer scalar type"""
    return src in SCALAR_TYPES

def is_bytes_type(src: str) -> bool:
    """Checks if a type name is a bytes or string type"""
    return src in ("bytes", "string")

@dataclass
class FieldType:
    """
    Represents a parsed Protocol Buffer field type with resolution information.
    Tracks whether the type is scalar, bytes/string, or a reference to a
    message/enum type, along with scope and import information.
    """
    src: str
    is_scalar: bool
    is_bytes: bool
    name: Optional[ScopedName]
    scope: ScopedName
    
    ref_local_enum: Optional['Enum'] = None
    ref_local_message: Optional['Message'] = None
    ref_external_enum: Optional['Enum'] = None
    ref_external_message: Optional['Message'] = None
    ref_import: Optional[ProtoFile] = None
    scope_ref: Optional[ProtoFile] = None

    @staticmethod
    def parse(scope: ScopedName, buf: ParserBuffer) -> FieldType:
        """
        Parses a field type from the buffer.
        Handles scalar types, bytes/string types, and message/enum references.
        """
        src = lex.field_type(buf)
        buf.skip_spaces()

        scalar = is_scalar_type(src)
        is_bytes = is_bytes_type(src)
        name = None
        if not scalar and not is_bytes:
            name = ScopedName(src)

        return FieldType(
            src=src,
            is_scalar=scalar,
            is_bytes=is_bytes,
            name=name,
            scope=scope,
        )

    def clone(self) -> FieldType:
        """Creates a deep copy of the FieldType"""
        return FieldType(
            src=self.src,
            is_scalar=self.is_scalar,
            is_bytes=self.is_bytes,
            name=self.name.clone() if self.name else None,
            scope=self.scope.clone(),
            ref_local_enum=self.ref_local_enum,
            ref_local_message=self.ref_local_message,
            ref_external_enum=self.ref_external_enum,
            ref_external_message=self.ref_external_message,
            ref_import=self.ref_import,
            scope_ref=self.scope_ref,
        )

    @property
    def is_enum(self) -> bool:
        """Returns whether this type references an enum (local or external)"""
        return self.ref_external_enum is not None or self.ref_local_enum is not None

    @property
    def is_msg(self) -> bool:
        """Returns whether this type references a message (local or external)"""
        return self.ref_external_message is not None or self.ref_local_message is not None