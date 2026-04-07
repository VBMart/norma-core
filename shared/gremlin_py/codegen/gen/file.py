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
# Created by ab, 25.11.2025

"""
Provides functionality for generating Python source files from Protocol Buffer definitions.
This module handles the conversion of .proto files into Python code, managing imports,
type definitions, and code generation.
"""
from typing import List, Optional, Set

from .. import parser
from .dataclass import PythonDataclass
from .enum import PythonEnum
from .imports import ImportCollector
from .output import FileOutput
from . import import_def as import_resolver


class PythonFile:
    """
    Represents a generated Python source file from a Protocol Buffer definition.
    Manages the conversion of Protocol Buffer types to Python types and handles
    code generation for the complete file.
    """

    def __init__(self, out_path: str, file: parser.ProtoFile, proto_root: str, target_root: str, project_root: str, gremlin_import_path: str):
        self.out_path = out_path
        self.file = file
        
        names: Set[str] = set()

        self.imports = self._init_imports(file, proto_root, target_root, project_root, names, gremlin_import_path)
        self.enums = self._init_enums(file, names)
        self.messages = self._init_messages(file, names)

        if self.enums:
            self.imports.append(import_resolver.PythonImport(None, "enum", "enum"))

    def write(self, out_file: FileOutput):
        """Write the generated Python code to the output file."""
        self._write_header(out_file)
        self._write_imports(out_file)
        self._write_enums(out_file)
        self._write_messages(out_file)

    def resolve_imports(self, files: List['PythonFile']):
        """Resolve imports between files after all files have been initialized."""
        for i in self.imports:
            i.resolve(files)

    def resolve_refs(self):
        """Resolve internal references within the file."""
        for s in self.messages:
            s.resolve(self)

    def find_enum_name(self, target: parser.Enum) -> Optional[str]:
        """Finds the fully qualified name of an enum type within this file."""
        for enum_item in self.enums:
            if enum_item.src == target:
                return enum_item.full_name
        return None

    def find_imported_enum_name(self, target_file: parser.ProtoFile, target_enum: parser.Enum) -> Optional[str]:
        """Finds the fully qualified name of an imported enum type."""
        for import_ref in self.imports:
            if import_ref.is_system:
                continue
            
            if import_ref.target and import_ref.target.file.path == target_file.path:
                found = import_ref.target.find_enum_name(target_enum)
                if found:
                    return f"{import_ref.alias}.{found}"
        return None

    def find_writer_name(self, target: parser.Message) -> Optional[str]:
        """Finds the fully qualified name of a message type within this file."""
        for msg_item in self.messages:
            if msg_item.source == target:
                return msg_item.full_writer_name
        return None

    def find_reader_name(self, target: parser.Message) -> Optional[str]:
        """Finds the fully qualified name of a message type within this file."""
        for msg_item in self.messages:
            if msg_item.source == target:
                return msg_item.full_reader_name
        return None

    def find_imported_writer_name(self, target_file: parser.ProtoFile, target_msg: parser.Message) -> Optional[str]:
        """Finds the fully qualified name of an imported message type."""
        for import_ref in self.imports:
            if import_ref.is_system:
                continue

            if import_ref.target and import_ref.target.file.path == target_file.path:
                found = import_ref.target.find_writer_name(target_msg)
                if found:
                    return f"{import_ref.alias}.{found}"
        return None

    def find_imported_reader_name(self, target_file: parser.ProtoFile, target_msg: parser.Message) -> Optional[str]:
        """Finds the fully qualified name of an imported message type."""
        for import_ref in self.imports:
            if import_ref.is_system:
                continue

            if import_ref.target and import_ref.target.file.path == target_file.path:
                found = import_ref.target.find_reader_name(target_msg)
                if found:
                    return f"{import_ref.alias}.{found}"
        return None

    def _init_imports(self, file: parser.ProtoFile, proto_root: str, target_root: str, project_root: str, names: Set[str], gremlin_import_path: str) -> List[import_resolver.PythonImport]:
        imports: List[import_resolver.PythonImport] = []
        
        imports.extend(self._init_system_imports(file, names, gremlin_import_path))

        used_imports = ImportCollector.collect_from_file(file)
        
        for import_file in used_imports:
            resolved = import_resolver.resolve_import(
                import_file, proto_root, target_root, project_root,
                import_file.path, names
            )
            imports.append(resolved)
            
        return imports

    def _init_system_imports(self, file: parser.ProtoFile, names: Set[str], gremlin_import_path: str) -> List[import_resolver.PythonImport]:
        """Initialize system imports (e.g., dataclasses, enum, typing)."""
        imports: List[import_resolver.PythonImport] = []
        
        if file.messages:
            imports.append(import_resolver.PythonImport(None, "dataclasses", "dataclasses"))
            imports.append(import_resolver.PythonImport(None, "typing", "typing"))
            imports.append(import_resolver.PythonImport(None, "gremlin", gremlin_import_path))
            

        for imp in imports:
            names.add(imp.alias)
        return imports

    def _init_enums(self, file: parser.ProtoFile, names: Set[str]) -> List[PythonEnum]:
        enums = []
        for enum_item in file.enums:
            enums.append(PythonEnum(enum_item, "", names))
        for msg in file.messages:
            self._collect_nested_enums(msg, enums, names, msg.name.name)
        return enums

    def _init_messages(self, file: parser.ProtoFile, names: Set[str]) -> List[PythonDataclass]:
        messages = []
        for msg in file.messages:
            messages.append(PythonDataclass(msg, names, ""))
            self._collect_nested_messages(msg, messages, names, msg.name.name)
        return messages

    def _collect_nested_enums(self, message: parser.Message, enums: List[PythonEnum], names: Set[str], scope: str):
        for enum_item in message.enums:
            enums.append(PythonEnum(enum_item, scope, names))
        for nested_message in message.messages:
            new_scope = f"{scope}_{nested_message.name.name}"
            self._collect_nested_enums(nested_message, enums, names, new_scope)

    def _collect_nested_messages(self, message: parser.Message, messages: List[PythonDataclass], names: Set[str], scope: str):
        for nested_message in message.messages:
            messages.append(PythonDataclass(nested_message, names, scope))
            new_scope = f"{scope}_{nested_message.name.name}"
            self._collect_nested_messages(nested_message, messages, names, new_scope)

    def _write_header(self, out_file: FileOutput):
        out_file.write_string("from __future__ import annotations")
        out_file.linebreak()
        out_file.write_string("# This file is generated by `gremlin_py`.")
        out_file.write_string("# DO NOT EDIT.")
        out_file.linebreak()

    def _write_imports(self, out_file: FileOutput):
        for import_ref in self.imports:
            out_file.write_string(import_ref.code())
        out_file.linebreak()

    def _write_enums(self, out_file: FileOutput):
        if not self.enums:
            return
        out_file.linebreak()
        out_file.write_comment("enums")
        for enum_item in self.enums:
            out_file.write_string(enum_item.create_enum_def())

    def _write_messages(self, out_file: FileOutput):
        if not self.messages:
            return
        out_file.linebreak()
        out_file.write_comment("messages")
        
        written_messages = set()
        for msg_item in self.messages:
            if msg_item.writer_name not in written_messages:
                msg_item.code(out_file)
                written_messages.add(msg_item.writer_name)