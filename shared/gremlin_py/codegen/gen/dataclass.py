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
Provides functionality for generating Python dataclasses from Protocol Buffer message definitions.
This module handles the generation of writer and reader dataclasses, field definitions,
nested types, and type resolution for Protocol Buffer messages.
"""
from __future__ import annotations
from typing import List, Optional, Set, Any, TYPE_CHECKING

from .. import parser
from .fields import naming
from .fields.struct_field import Field, FieldBuilder
from .output import FileOutput
from .dataclass_codegen import CodeGenerator

if TYPE_CHECKING:
    from .file import PythonFile

class PythonDataclass:
    """
    Represents a Python dataclass generated from a Protocol Buffer message.
    It manages both the writer and reader variants of the dataclass, along with
    any nested types (enums, dataclasses) and fields.
    """

    def __init__(self, src: parser.Message, names: Set[str], scope_name: str):
        self.source = src

        names_result = NameGenerator.generate(src.name.name, scope_name, names)
        
        self.writer_name = names_result.writer_name
        self.reader_name = names_result.reader_name
        self.full_writer_name = names_result.full_writer_name
        self.full_reader_name = names_result.full_reader_name

        scope_names: Set[str] = {"calc_protobuf_size", "encode"}
        fields_result = FieldsBuilder.build(src, self.full_writer_name, self.writer_name, self.reader_name, scope_names)

        self.fields: List[Field] = fields_result.fields

    def code(self, out_file: FileOutput):
        """Generates code for the dataclass"""
        code_gen = CodeGenerator(self, out_file)
        code_gen.generate()

    def resolve(self, file: "PythonFile"):
        """Resolves type references in the dataclass's fields"""
        # Resolve field types
        for field in self.fields:
            if hasattr(field, 'target_type'):
                if field.target_type.is_enum:
                    enum_name = TypeResolver.resolve_enum(file, field.target_type)
                    if enum_name:
                        field.resolve(enum_name)
                elif field.target_type.is_msg:
                    writer_name, reader_name = TypeResolver.resolve_message(file, field.target_type)
                    if writer_name and reader_name:
                        field.resolve(writer_name, reader_name)
            elif hasattr(field, 'value_type'): # For maps
                if field.value_type.is_enum:
                    enum_name = TypeResolver.resolve_enum(file, field.value_type)
                    if enum_name:
                        field.resolve_enum_value(enum_name)
                elif field.value_type.is_msg:
                    writer_name, reader_name = TypeResolver.resolve_message(file, field.value_type)
                    if writer_name and reader_name:
                        field.resolve_message_value(writer_name, reader_name)


class NameGenerator:
    """Helper for generating dataclass names"""
    
    class Names:
        def __init__(self, writer_name: str, reader_name: str,
                     full_writer_name: str, full_reader_name: str):
            self.writer_name = writer_name
            self.reader_name = reader_name
            self.full_writer_name = full_writer_name
            self.full_reader_name = full_reader_name

    @staticmethod
    def generate(name: str, scope_name: str, names: Set[str]) -> NameGenerator.Names:
        prefixed_name = f"{scope_name}$${name}" if scope_name else name
        const_name = naming.struct_name(prefixed_name, names)

        writer_name = const_name
        reader_name = f"{const_name}Reader"

        return NameGenerator.Names(
            writer_name=writer_name,
            reader_name=reader_name,
            full_writer_name=writer_name,
            full_reader_name=reader_name,
        )


class FieldsBuilder:
    """Helper for building fields and nested types"""

    class Result:
        def __init__(self):
            self.fields: List[Any] = []

    @staticmethod
    def build(src: parser.Message, scope_name: str, 
              writer_struct_name: str, reader_struct_name: str, scope_names: Set[str]) -> FieldsBuilder.Result:
        
        result = FieldsBuilder.Result()

        FieldsBuilder._build_fields(result, src, scope_names, writer_struct_name, reader_struct_name)

        return result


    @staticmethod
    def _build_fields(result: FieldsBuilder.Result, src: parser.Message, scope_names: Set[str],
                      writer_struct_name: str, reader_struct_name: str):
        
        FieldBuilder.create_normal_fields(result.fields, src, scope_names, writer_struct_name, reader_struct_name)
        FieldBuilder.create_one_of_fields(result.fields, src, scope_names, writer_struct_name, reader_struct_name)
        FieldBuilder.create_map_fields(result.fields, src, scope_names, writer_struct_name, reader_struct_name)


class TypeResolver:
    """Helper for resolving type references"""

    @staticmethod
    def resolve_enum(file: "PythonFile", target_type: parser.FieldType) -> Optional[str]:
        if target_type.ref_local_enum:
            return file.find_enum_name(target_type.ref_local_enum)
        elif target_type.ref_external_enum:
            return file.find_imported_enum_name(target_type.ref_import, target_type.ref_external_enum)
        return None

    @staticmethod
    def resolve_message(file: "PythonFile", target_type: parser.FieldType) -> (Optional[str], Optional[str]):
        if target_type.ref_local_message:
            return file.find_writer_name(target_type.ref_local_message), file.find_reader_name(target_type.ref_local_message)
        elif target_type.ref_external_message:
            return file.find_imported_writer_name(target_type.ref_import, target_type.ref_external_message), file.find_imported_reader_name(target_type.ref_import, target_type.ref_external_message)
        return None, None
