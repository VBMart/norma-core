# //! This module handles the generation of Python code for repeated scalar fields.
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

from typing import Optional, List, Set

from ... import parser
from . import naming
from . import scalar
from . import sizes

class PythonRepeatedScalarField:
    """
    Represents a Protocol Buffer repeated scalar field in Python.
    Handles both packed and unpacked encoding formats.
    """

    def __init__(
        self,
        field_name: str,
        field_type: str,
        field_opts: Optional[List[parser.Option]],
        field_index: int,
        names: Set[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ):
        # Generate field names
        name = naming.struct_field_name(field_name, names)
        
        # Generate reader method name
        reader_prefixed = f"get_{field_name}"
        reader_method_name = naming.struct_method_name(reader_prefixed, names)

        # Get Python type mapping
        python_type = scalar.SCALAR_PYTHON_TYPE[field_type]

        self.field_type = field_type
        self.python_type = python_type
        self.size_func_name: Optional[str] = None
        if field_type not in ["fixed32", "sfixed32", "float", "fixed64", "sfixed64", "double", "bool"]:
            self.size_func_name = scalar.SCALAR_SIZE_FN[field_type]
        self.write_func_name = scalar.SCALAR_WRITER_FN[field_type]
        self.read_func_name = scalar.SCALAR_READER_FN[field_type]

        self.writer_field_name = name
        self.reader_field_name = f"_{name}"
        self.reader_method_name = reader_method_name
        self.reader_offsets_name = f"_{name}_offsets"
        self.reader_wires_name = f"_{name}_wires"

        self.wire_index = field_index

        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name

    def create_writer_struct_field(self) -> str:
        """Generate writer struct field declaration"""
        return f"{self.writer_field_name}: typing.Optional[list[{self.python_type}]] = None"

    def create_size_check(self) -> str:
        """
        Generate size calculation code for serialization.
        Handles special cases for empty arrays, single values, and packed encoding.
        """
        size_of_one = ""
        elif_block = ""

        match self.field_type:
            case "fixed32" | "sfixed32" | "float":
                size_of_one = "4"
                wire_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.FIXED32)
                elif_block = (f"    elif len(arr) > 1:\n"
                              f"        packed_size = len(arr) * 4\n"
                              f"        res += {wire_size} + (((packed_size | 1).bit_length() + 6) // 7) + packed_size")
            case "fixed64" | "sfixed64" | "double":
                size_of_one = "8"
                wire_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.FIXED64)
                elif_block = (f"    elif len(arr) > 1:\n"
                              f"        packed_size = len(arr) * 8\n"
                              f"        res += {wire_size} + (((packed_size | 1).bit_length() + 6) // 7) + packed_size")
            case "bool":
                size_of_one = "1"
                wire_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)
                elif_block = (f"    elif len(arr) > 1:\n"
                              f"        packed_size = len(arr)\n"
                              f"        res += {wire_size} + (((packed_size | 1).bit_length() + 6) // 7) + packed_size")
            case _:
                wire_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)
                size_of_one = f"{self.size_func_name}(arr[0])"
                elif_block = (f"    elif len(arr) > 1:\n"
                              f"        packed_size = 0\n"
                              f"        for v in arr:\n"
                              f"            packed_size += {self.size_func_name}(v)\n"
                              f"        res += {wire_size} + (((packed_size | 1).bit_length() + 6) // 7) + packed_size")

        wire_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)
        return (f"if self.{self.writer_field_name}:\n"
                f"    arr = self.{self.writer_field_name}\n"
                f"    if len(arr) == 1:\n"
                f"        res += {wire_size} + {size_of_one}\n"
                f"{elif_block}")

    def create_writer(self) -> str:
        """
        Generate serialization code.
        Uses packed encoding for multiple values and optimized single-value encoding.
        """
        elif_block = ""
        match self.field_type:
            case "fixed32" | "sfixed32" | "float":
                elif_block = f"        packed_size = len(arr) * 4"
            case "fixed64" | "sfixed64" | "double":
                elif_block = f"        packed_size = len(arr) * 8"
            case "bool":
                elif_block = f"        packed_size = len(arr)"
            case _:
                elif_block = (f"        packed_size = 0\n"
                              f"        for v in arr:\n"
                              f"            packed_size += {self.size_func_name}(v)")

        return (f"if self.{self.writer_field_name}:\n"
                f"    arr = self.{self.writer_field_name}\n"
                f"    if len(arr) == 1:\n"
                f"        target.{self.write_func_name}({self.wire_index}, arr[0])\n"
                f"    elif len(arr) > 1:\n"
                f"{elif_block}\n"
                f"        target.append_bytes_tag({self.wire_index}, packed_size)\n"
                f"        for v in arr:\n"
                f"            target.{self.write_func_name}_without_tag(v)")

    def create_reader_struct_field(self) -> str:
        """
        Generate reader struct field declaration.
        Uses separate arrays for offsets and wire types to support both encoding formats.
        """
        return (f"self.{self.reader_offsets_name}: typing.Optional[list[int]] = None\n"
                f"self.{self.reader_wires_name}: typing.Optional[list[gremlin.ProtoWireType]] = None")

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
                f"            result = self._buf.{self.read_func_name}(offset)\n"
                f"            offset += result.size")

    def create_reader_method(self) -> str:
        """
        Generate getter method that processes stored offsets.
        Handles both packed and unpacked formats transparently.
        """
        return (f"def {self.reader_method_name}(self) -> list[{self.python_type}]:\n"
                f"    if self.{self.reader_offsets_name}:\n"
                f"        result: list[{self.python_type}] = []\n"
                f"        for start_offset, wire_type in zip(self.{self.reader_offsets_name}, self.{self.reader_wires_name}):\n"
                f"            if wire_type == gremlin.ProtoWireType.BYTES:\n"
                f"                length_result = self._buf.read_varint(start_offset)\n"
                f"                offset = start_offset + length_result.size\n"
                f"                end_offset = offset + length_result.value\n"
                f"                while offset < end_offset:\n"
                f"                    value_result = self._buf.{self.read_func_name}(offset)\n"
                f"                    result.append(value_result.value)\n"
                f"                    offset += value_result.size\n"
                f"            else:\n"
                f"                value_result = self._buf.{self.read_func_name}(start_offset)\n"
                f"                result.append(value_result.value)\n"
                f"        return result\n"
                f"    return []")