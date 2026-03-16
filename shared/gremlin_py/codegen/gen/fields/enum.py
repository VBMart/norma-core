# This module handles the generation of Python code for Protocol Buffer enum fields.
# It provides functionality to create reader and writer methods for enum fields,
# handle default values, and manage wire format encoding.
# Enums are serialized as int32 values in the Protocol Buffer wire format.

from ... import parser
from . import naming
from . import sizes

class PythonEnumField:
    """
    Represents a Protocol Buffer enum field in Python, managing both reading and writing
    of the field along with wire format details.
    """

    def __init__(self, field_name: str, field_type: parser.FieldType, field_opts: list[parser.Option] | None,
                 field_index: int, names: set[str], writer_struct_name: str,
                 reader_struct_name: str):
        
        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name
        self.target_type = field_type
        self.resolved_enum: str | None = None
        self.custom_default: str | None = None

        self.writer_field_name = naming.struct_field_name(field_name, names)
        
        reader_prefixed = f"get_{field_name}"
        self.reader_method_name = naming.struct_method_name(reader_prefixed, names)
        self.reader_field_name = f"_{self.writer_field_name}"

        if field_opts:
            for opt in field_opts:
                if opt.name == "default":
                    self.custom_default = opt.value
                    break
        
        self.wire_index = field_index

    def resolve(self, resolved_enum: str):
        """Set the resolved enum type name after type resolution phase"""
        self.resolved_enum = resolved_enum

    def create_writer_struct_field(self) -> str:
        """Generate writer struct field declaration with default value of 0"""
        return f"{self.writer_field_name}: {self.resolved_enum} = {self.resolved_enum}(0)"

    def create_size_check(self) -> str:
        """Generate size calculation code for serialization"""
        field_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)
        
        default_value = f"{self.resolved_enum}.{self.custom_default}" if self.custom_default else f"{self.resolved_enum}(0)"
        return (f"if self.{self.writer_field_name} != {default_value}:\n"
                f"    res += {field_size} + (((self.{self.writer_field_name}.value | 1).bit_length() + 6) // 7)")

    def create_writer(self) -> str:
        """Generate serialization code"""
        bytes_tag = sizes.generate_tag_bytes(self.wire_index, sizes.ProtoWireType.VARINT)
        default_value = f"{self.resolved_enum}.{self.custom_default}" if self.custom_default else f"{self.resolved_enum}(0)"
        return (f"if self.{self.writer_field_name} != {default_value}:\n"
                f"    target.append_int32({bytes_tag}, self.{self.writer_field_name}.value)")

    def create_reader_struct_field(self) -> str:
        """Generate reader struct field declaration with default value"""
        if self.custom_default:
            full_default = f"{self.resolved_enum}.{self.custom_default}"
            return f"self.{self.reader_field_name}: {self.resolved_enum} = {full_default}"
        else:
            return f"self.{self.reader_field_name}: {self.resolved_enum} = {self.resolved_enum}(0)"

    def create_reader_case(self) -> str:
        """Generate deserialization case statement"""
        return (f"    case {self.wire_index}:\n"
                f"        result = self._buf.read_int32(offset)\n"
                f"        offset += result.size\n"
                f"        self.{self.reader_field_name} = {self.resolved_enum}(result.value)")

    def create_reader_method(self) -> str:
        """Generate getter method for the field"""
        return (f"def {self.reader_method_name}(self) -> {self.resolved_enum}:\n"
                f"    return self.{self.reader_field_name}")