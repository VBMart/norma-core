# This module handles the generation of Python code for repeated enum fields in Protocol Buffers.
# Repeated enum fields can appear zero or more times in a message and support packing optimization.
# When packed, multiple enum values are encoded together in a single length-delimited field.
# The module supports both packed and unpacked representations for backward compatibility.

from ... import parser
from . import naming
from . import sizes

class PythonRepeatedEnumField:
    """
    Represents a repeated enum field in Protocol Buffers.
    Handles both packed and unpacked encoding formats, with a specialized
    reader implementation to support both formats transparently.
    """

    def __init__(self, field_name: str, field_type: parser.FieldType, field_index: int,
                 names: set[str], writer_struct_name: str,
                 reader_struct_name: str):
        
        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name
        self.target_type = field_type
        self.resolved_enum: str | None = None

        self.writer_field_name = naming.struct_field_name(field_name, names)
        
        reader_prefixed = f"get_{field_name}"
        self.reader_method_name = naming.struct_method_name(reader_prefixed, names)
        
        self._reader_field_name = f"_{self.writer_field_name}"
        self.reader_offsets_name = f"_{self.writer_field_name}_offsets"
        self.reader_wires_name = f"_{self.writer_field_name}_wires"
        
        self.wire_index = field_index

    def resolve(self, resolved_enum: str):
        """Set the resolved enum type name after type resolution phase"""
        self.resolved_enum = resolved_enum

    def create_writer_struct_field(self) -> str:
        """Generate writer struct field declaration"""
        return f"{self.writer_field_name}: list[{self.resolved_enum}] | None = None"

    def create_size_check(self) -> str:
        """
        Generate size calculation code for serialization.
        Handles special cases for empty arrays, single values, and packed encoding.
        """
        wire_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)
        return (f"if self.{self.writer_field_name}:\n"
                f"    arr = self.{self.writer_field_name}\n"
                f"    if len(arr) == 1:\n"
                f"        res += {wire_size} + (((arr[0].value | 1).bit_length() + 6) // 7)\n"
                f"    elif len(arr) > 1:\n"
                f"        packed_size = 0\n"
                f"        for v in arr:\n"
                f"            packed_size += ((v.value | 1).bit_length() + 6) // 7\n"
                f"        res += {wire_size} + (((packed_size | 1).bit_length() + 6) // 7) + packed_size")

    def create_writer(self) -> str:
        """
        Generate serialization code.
        Uses packed encoding for multiple values for efficiency.
        """
        bytes_tag = sizes.generate_tag_bytes(self.wire_index, sizes.ProtoWireType.VARINT)
        packed_tag = sizes.generate_tag_bytes(self.wire_index, sizes.ProtoWireType.BYTES)

        return (f"if self.{self.writer_field_name}:\n"
                f"    arr = self.{self.writer_field_name}\n"
                f"    if len(arr) == 1:\n"
                f"        target.append_int32({bytes_tag}, arr[0].value)\n"
                f"    elif len(arr) > 1:\n"
                f"        packed_size = 0\n"
                f"        for v in arr:\n"
                f"            packed_size += gremlin.sizes.size_i32(v.value)\n"
                f"        target.append_bytes_size_with_tag({packed_tag}, packed_size)\n"
                f"        for v in arr:\n"
                f"            target.append_int32_without_tag(v.value)")

    def create_reader_struct_field(self) -> str:
        """
        Generate reader struct field declaration.
        Uses separate arrays for offsets and wire types to support both encoding formats.
        """
        return (
            f"self.{self.reader_offsets_name}: list[int] | None = None\n"
            f"self.{self.reader_wires_name}: list[gremlin.ProtoWireType] | None = None"
        )

    def create_reader_case(self) -> str:
        """
        Generate deserialization case statement.
        Stores offset and wire type information for later processing.
        """
        return (f"    case {self.wire_index}:\n"
                f"        if self.{self.reader_offsets_name} is None:\n"
                f"            self.{self.reader_offsets_name} = []\n"
                f"            self.{self.reader_wires_name} = []\n"
                f"        self.{self.reader_offsets_name}.append(offset)\n"
                f"        self.{self.reader_wires_name}.append(tag.wire)\n"
                f"        if tag.wire == gremlin.ProtoWireType.BYTES:\n"
                f"            length_result = self._buf.read_varint(offset)\n"
                f"            offset += length_result.size + length_result.value\n"
                f"        else:\n"
                f"            result = self._buf.read_int32(offset)\n"
                f"            offset += result.size")

    def create_reader_method(self) -> str:
        """
        Generate getter method that constructs enum array from stored offsets.
        Handles both packed and unpacked formats transparently.
        """
        return (
            f"def {self.reader_method_name}(self) -> list[{self.resolved_enum}]:\n"
            f"    if self.{self.reader_offsets_name}:\n"
            f"        result = []\n"
            f"        for start_offset, wire_type in zip(self.{self.reader_offsets_name}, self.{self.reader_wires_name}):\n"
            f"            if wire_type == gremlin.ProtoWireType.BYTES:\n"
            f"                length_result = self._buf.read_varint(start_offset)\n"
            f"                offset = start_offset + length_result.size\n"
            f"                end_offset = offset + length_result.value\n"
            f"                while offset < end_offset:\n"
            f"                    value_result = self._buf.read_int32(offset)\n"
            f"                    result.append({self.resolved_enum}(value_result.value))\n"
            f"                    offset += value_result.size\n"
            f"            else:\n"
            f"                value_result = self._buf.read_int32(start_offset)\n"
            f"                result.append({self.resolved_enum}(value_result.value))\n"
            f"        return result\n"
            f"    return []"
        )