"""
This module handles type resolution and extension handling for Protocol Buffer files.
It provides functionality to:
- Find and resolve message and enum types across files
- Handle message extensions and field inheritance
- Set up parent-child relationships between nested types
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
from typing import List, Optional

from .entries.file import ProtoFile
from .entries.message import Message
from .entries.enum import Enum
from .entries.extend import Extend
from .entries.scoped_name import ScopedName
from .entries.field_type import FieldType
from .entries.errors import ParsingError, ProtoError

@dataclass
class ExtendBase:
    """Represents a message that can be extended and its containing file"""
    message: Message
    file: ProtoFile

def resolve_references(files: List[ProtoFile]) -> None:
    """
    Resolve all type references and extensions across a set of proto files.
    This is done in two passes:
    1. Resolve all extensions to handle field inheritance
    2. Resolve all type references to link fields to their type definitions
    """
    for file in files:
        resolve_extend(file)

    for file in files:
        resolve_refs(file)

def find_enum_in_message(message: Message, name: ScopedName) -> Optional[Enum]:
    """Find an enum definition within a message and its nested messages"""
    for e in message.enums:
        if e.name == name:
            return e

    for msg in message.messages:
        res = find_enum_in_message(msg, name)
        if res:
            return res

    return None

def find_enum(file: ProtoFile, name: ScopedName) -> Optional[Enum]:
    """Find an enum definition within a proto file"""
    for e in file.enums:
        if e.name == name:
            return e

    for msg in file.messages:
        res = find_enum_in_message(msg, name)
        if res:
            return res

    return None

def find_message_in_message(message: Message, name: ScopedName) -> Optional[Message]:
    """Find a message definition within another message"""
    if message.name == name:
        return message

    for msg in message.messages:
        res = find_message_in_message(msg, name)
        if res:
            return res

    return None

def find_message(file: ProtoFile, name: ScopedName) -> Optional[Message]:
    """Find a message definition within a proto file"""
    for msg in file.messages:
        res = find_message_in_message(msg, name)
        if res:
            return res
    return None

def find_extend_in_message(message: Message, name: ScopedName) -> Optional[Message]:
    """Find an extendable message within another message"""
    if message.name == name:
        return message

    for msg in message.messages:
        res = find_extend_in_message(msg, name)
        if res:
            return res

    return None

def find_extend_message(file: ProtoFile, name: ScopedName) -> Optional[Message]:
    """Find a message that can be extended within a proto file"""
    for msg in file.messages:
        res = find_extend_in_message(msg, name)
        if res and not res.extends:
            return res
    return None

def find_local_extend_source(file: ProtoFile, message_name: ScopedName, extend_base: ScopedName) -> Optional[Message]:
    """Find a local message that is being extended within the same file"""
    search_path = message_name.clone()

    while search_path:
        name = extend_base.to_scope(search_path)

        for msg in file.messages:
            res = find_extend_in_message(msg, name)
            if res:
                return res

        search_path = search_path.get_parent

    return None

def find_extend_base(file: ProtoFile, message: Message, ext: Extend) -> Optional[ExtendBase]:
    """Find the base message that is being extended"""
    local = find_local_extend_source(file, message.name, ext.base)
    if local:
        return ExtendBase(message=local, file=file)

    for imp in file.imports:
        if imp.target:
            res = find_extend_message(imp.target, ext.base)
            if res:
                return ExtendBase(message=res, file=imp.target)

    return None

def copy_extended_fields(message: Message, target: ExtendBase) -> None:
    """Copy fields from extended message into the extending message"""
    for source_field in target.message.fields:
        if not any(f.f_name == source_field.f_name for f in message.fields):
            new_field = source_field.clone()
            new_field.f_type.scope_ref = target.file
            message.fields.append(new_field)

    for source_map in target.message.maps:
        if not any(m.f_name == source_map.f_name for m in message.maps):
            new_map = source_map.clone()
            new_map.value_type.scope_ref = target.file
            message.maps.append(new_map)

    for source_oneof in target.message.oneofs:
        if not any(o.name == source_oneof.name for o in message.oneofs):
            new_oneof = source_oneof.clone()
            for field in new_oneof.fields:
                field.f_type.scope_ref = target.file
            message.oneofs.append(new_oneof)

def resolve_message_extend(file: ProtoFile, message: Message) -> None:
    """Resolve message extension relationships"""
    for ext in message.extends:
        target = find_extend_base(file, message, ext)
        if target:
            copy_extended_fields(message, target)
        else:
            raise ProtoError(ParsingError.ExtendSourceNotFound)

    for msg in message.messages:
        resolve_message_extend(file, msg)

def resolve_local_type(file: ProtoFile, ftype: FieldType) -> bool:
    """Attempt to resolve a type locally within the same file"""
    if not ftype.name:
        return False

    search_path = ftype.scope.clone()
    while search_path:
        name = ftype.name.to_scope(search_path)
        target_file = ftype.scope_ref or file

        res_enum = find_enum(target_file, name)
        if res_enum:
            ftype.ref_local_enum = res_enum
            return True

        res_msg = find_message(target_file, name)
        if res_msg:
            ftype.ref_local_message = res_msg
            return True
        
        search_path = search_path.get_parent

    return False

def resolve_external_type(file: ProtoFile, ftype: FieldType) -> bool:
    """Attempt to resolve a type in imported files"""
    if not ftype.name:
        return False

    target_file = ftype.scope_ref or file

    for imp in target_file.imports:
        if imp.target:
            search_path = ftype.scope.clone()
            while search_path:
                local_name = ftype.name.to_scope(search_path)

                res_enum = find_enum(imp.target, local_name)
                if res_enum:
                    ftype.ref_external_enum = res_enum
                    ftype.ref_import = imp.target
                    return True

                res_msg = find_message(imp.target, local_name)
                if res_msg:
                    ftype.ref_external_message = res_msg
                    ftype.ref_import = imp.target
                    return True
                
                search_path = search_path.get_parent

    return False

def resolve_type(file: ProtoFile, ftype: FieldType) -> None:
    """Resolve a field type to its definition"""
    if ftype.is_scalar or ftype.is_bytes:
        return

    if resolve_local_type(file, ftype):
        return
    
    if resolve_external_type(file, ftype):
        return

    raise ProtoError(ParsingError.TypeNotFound, f"Type '{ftype.src}' not found in scope '{ftype.scope}'")

def resolve_message_fields(file: ProtoFile, message: Message) -> None:
    """Resolve all field types within a message and its nested messages"""
    for f in message.fields:
        resolve_type(file, f.f_type)

    for f in message.maps:
        resolve_type(file, f.value_type)

    for o in message.oneofs:
        for f in o.fields:
            resolve_type(file, f.f_type)

    for msg in message.messages:
        resolve_message_fields(file, msg)

def resolve_message_parents(message: Message) -> None:
    """Set up parent-child relationships between messages and their nested types"""
    for msg in message.messages:
        msg.parent = message
        resolve_message_parents(msg)
    
    for e in message.enums:
        e.parent = message

def resolve_extend(file: ProtoFile) -> None:
    """Resolve extensions in a file"""
    for message in file.messages:
        resolve_message_extend(file, message)

def resolve_refs(file: ProtoFile) -> None:
    """Resolve all type references in a file"""
    for message in file.messages:
        resolve_message_fields(file, message)
        resolve_message_parents(message)