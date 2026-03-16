"""
This module provides a unified interface for handling different types of Protocol Buffer fields
in Python. It acts as a facade over specialized field implementations, handling field type
detection and delegation to appropriate handlers. The module supports all Protocol Buffer field
types including scalar, bytes, message, enum, repeated fields, and maps.
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
# Created by ab, 25.11.2025

from __future__ import annotations
from typing import Union

from ... import parser

from .scalar import PythonScalarField
from .bytes import PythonBytesField
from .message import PythonMessageField
from .enum import PythonEnumField
from .repeated_bytes import PythonRepeatedBytesField
from .repeated_message import PythonRepeatedMessageField
from .repeated_enum import PythonRepeatedEnumField
from .repeated_scalar import PythonRepeatedScalarField
from .map import PythonMapField

Field = Union[
    PythonScalarField,
    PythonBytesField,
    PythonMessageField,
    PythonEnumField,
    PythonRepeatedBytesField,
    PythonRepeatedMessageField,
    PythonRepeatedEnumField,
    PythonRepeatedScalarField,
    PythonMapField,
]


class FieldBuilder:
    @staticmethod
    def create_normal_fields(
        fields_list: list[Field],
        src: parser.Message,
        scope: list[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ):
        for mf in src.fields:
            if mf.repeated:
                field = FieldBuilder.create_repeated_field(
                    mf, scope, writer_struct_name, reader_struct_name
                )
            else:
                field = FieldBuilder.create_single_field(
                    mf, scope, writer_struct_name, reader_struct_name
                )
            fields_list.append(field)

    @staticmethod
    def create_one_of_fields(
        fields_list: list[Field],
        src: parser.Message,
        scope: list[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ):
        for of in src.oneofs:
            for mf in of.fields:
                field = FieldBuilder.create_one_of_field(
                    mf, scope, writer_struct_name, reader_struct_name
                )
                fields_list.append(field)

    @staticmethod
    def create_map_fields(
        fields_list: list[Field],
        src: parser.Message,
        scope: list[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ):
        for map_field in src.maps:
            field = PythonMapField(
                map_field,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
            fields_list.append(field)

    @staticmethod
    def create_repeated_field(
        mf: parser.fields.NormalField,
        scope: list[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ) -> Field:
        if mf.f_type.is_scalar:
            return PythonRepeatedScalarField(
                mf.f_name,
                mf.f_type.src,
                mf.options,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        elif mf.f_type.is_bytes:
            return PythonRepeatedBytesField(
                mf.f_name,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
                is_string=mf.f_type.src == "string",
            )
        elif mf.f_type.is_enum:
            return PythonRepeatedEnumField(
                mf.f_name,
                mf.f_type,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        elif mf.f_type.is_msg:
            return PythonRepeatedMessageField(
                mf.f_name,
                mf.f_type,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        raise TypeError(f"Unsupported repeated field type: {mf.f_type}")

    @staticmethod
    def create_single_field(
        mf: parser.fields.NormalField,
        scope: list[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ) -> Field:
        if mf.f_type.is_scalar:
            return PythonScalarField(
                mf.f_name,
                mf.f_type.src,
                mf.options,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        elif mf.f_type.is_bytes:
            return PythonBytesField(
                mf.f_name,
                mf.options,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
                is_string=mf.f_type.src == "string",
            )
        elif mf.f_type.is_enum:
            return PythonEnumField(
                mf.f_name,
                mf.f_type,
                mf.options,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        elif mf.f_type.is_msg:
            return PythonMessageField(
                mf.f_name,
                mf.f_type,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        raise TypeError(f"Unsupported field type: {mf.f_type}")

    @staticmethod
    def create_one_of_field(
        mf: parser.fields.OneOfField,
        scope: list[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ) -> Field:
        if mf.f_type.is_scalar:
            return PythonScalarField(
                mf.f_name,
                mf.f_type.src,
                mf.options,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        elif mf.f_type.is_bytes:
            return PythonBytesField(
                mf.f_name,
                mf.options,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
                is_string=mf.f_type.src == "string",
            )
        elif mf.f_type.is_enum:
            return PythonEnumField(
                mf.f_name,
                mf.f_type,
                mf.options,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        elif mf.f_type.is_msg:
            return PythonMessageField(
                mf.f_name,
                mf.f_type,
                mf.index,
                scope,
                writer_struct_name,
                reader_struct_name,
            )
        raise TypeError(f"Unsupported oneof field type: {mf.f_type}")