# //! This module handles the generation of Python code for Protocol Buffer scalar fields.
# //! It provides mappings between Protocol Buffer scalar types and their Python equivalents,
# //! along with support for default values and specialized encoding/decoding functions.
# //! Scalar fields include numeric types (integers and floats) and booleans.

#               .'\   /`.
#             .'.-.`-'.-.`.
#        ..._:   .-. .-.   :_...
#      .'    '-.(o ) (o ).-'    `.
#     :  _    _ _`~(_)~`_ _    _  :
#    :  /:   ' .-/_   _\-. `   ;\  :
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
from . import sizes

# Maps Protocol Buffer scalar types to their corresponding Python types
SCALAR_PYTHON_TYPE = {
    "bool": "bool",
    "float": "float",
    "double": "float",
    "int32": "int",
    "int64": "int",
    "uint32": "int",
    "uint64": "int",
    "sint32": "int",
    "sint64": "int",
    "fixed32": "int",
    "fixed64": "int",
    "sfixed32": "int",
    "sfixed64": "int",
}

# Returns the default value for each Protocol Buffer scalar type
SCALAR_DEFAULT_VALUE = {
    "bool": "False",
    "float": "0.0",
    "double": "0.0",
    "int32": "0",
    "int64": "0",
    "uint32": "0",
    "uint64": "0",
    "sint32": "0",
    "sint64": "0",
    "fixed32": "0",
    "fixed64": "0",
    "sfixed32": "0",
    "sfixed64": "0",
}

# Returns the size calculation function name for each Protocol Buffer scalar type
SCALAR_SIZE_FN = {
    "int32": "gremlin.sizes.size_i32",
    "int64": "gremlin.sizes.size_i64",
    "uint32": "gremlin.sizes.size_varint",
    "uint64": "gremlin.sizes.size_varint",
    "sint32": "gremlin.sizes.size_signed_varint",
    "sint64": "gremlin.sizes.size_signed_varint",
}

# Returns the serialization function name for each Protocol Buffer scalar type
SCALAR_WRITER_FN = {
    "bool": "append_bool",
    "float": "append_float32",
    "double": "append_float64",
    "int32": "append_int32",
    "int64": "append_int64",
    "uint32": "append_uint32",
    "uint64": "append_uint64",
    "sint32": "append_sint32",
    "sint64": "append_sint64",
    "fixed32": "append_fixed32",
    "fixed64": "append_fixed64",
    "sfixed32": "append_sfixed32",
    "sfixed64": "append_sfixed64",
}

# Returns the deserialization function name for each Protocol Buffer scalar type
SCALAR_READER_FN = {
    "bool": "read_bool",
    "float": "read_float32",
    "double": "read_float64",
    "int32": "read_int32",
    "int64": "read_int64",
    "uint32": "read_uint32",
    "uint64": "read_uint64",
    "sint32": "read_sint32",
    "sint64": "read_sint64",
    "fixed32": "read_fixed32",
    "fixed64": "read_fixed64",
    "sfixed32": "read_sfixed32",
    "sfixed64": "read_sfixed64",
}

WIRE_TYPES = {
    "bool": sizes.ProtoWireType.VARINT,
    "float": sizes.ProtoWireType.FIXED32,
    "double": sizes.ProtoWireType.FIXED64,
    "int32": sizes.ProtoWireType.VARINT,
    "int64": sizes.ProtoWireType.VARINT,
    "uint32": sizes.ProtoWireType.VARINT,
    "uint64": sizes.ProtoWireType.VARINT,
    "sint32": sizes.ProtoWireType.VARINT,
    "sint64": sizes.ProtoWireType.VARINT,
    "fixed32": sizes.ProtoWireType.FIXED32,
    "fixed64": sizes.ProtoWireType.FIXED64,
    "sfixed32": sizes.ProtoWireType.FIXED32,
    "sfixed64": sizes.ProtoWireType.FIXED64,
}

def _convert_scalar_default(value: str, python_type: str) -> str:
    """
    Converts Protocol Buffer scalar default value strings to Python expressions.
    Handles special floating point values (inf, -inf, nan).
    """
    lower_cased = value.lower()
    if python_type == "bool":
        if lower_cased == "true":
            return "True"
        if lower_cased == "false":
            return "False"
    if lower_cased == "inf":
        return "float('inf')"
    if lower_cased == "-inf":
        return "float('-inf')"
    if lower_cased == "nan":
        return "float('nan')"
    return value


class PythonScalarField:
    """
    Represents a Protocol Buffer scalar field in Python.
    Handles serialization, deserialization, and default values for scalar types.
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
        python_type = SCALAR_PYTHON_TYPE[field_type]

        # Process default value if present
        custom_default: Optional[str] = None
        if field_opts:
            for opt in field_opts:
                if opt.name == "default":
                    custom_default = _convert_scalar_default(opt.value, python_type)
                    break

        self.field_type = field_type
        self.python_type = python_type
        self.type_default = SCALAR_DEFAULT_VALUE[field_type]
        self.custom_default = custom_default
        self.write_func_name = SCALAR_WRITER_FN[field_type]
        self.read_func_name = SCALAR_READER_FN[field_type]
        self.writer_field_name = name
        self.reader_field_name = f"_{name}"
        self.reader_method_name = reader_method_name
        self.wire_index = field_index
        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name

    def create_writer_struct_field(self) -> str:
        """Generate writer struct field declaration with appropriate default"""
        return f"{self.writer_field_name}: {self.python_type} = {self.type_default}"

    def create_size_check(self) -> str:
        """
        Generate size calculation code.
        Only includes field in output if value differs from default.
        """
        default_value = self.custom_default if self.custom_default is not None else self.type_default
        field_size = sizes.size_field_tag(self.wire_index, WIRE_TYPES[self.field_type])
        match self.field_type:
            case "bool":
                field_size += 1
                if default_value == "True":
                    return (f"if not self.{self.writer_field_name}:\n"
                            f"    res += {field_size}")
                else:
                    return (f"if self.{self.writer_field_name}:\n"
                            f"    res += {field_size}")
            case "fixed32" | "sfixed32" | "float":
                field_size += 4
                return (f"if self.{self.writer_field_name} != {default_value}:\n"
                        f"    res += {field_size}")
            case "fixed64" | "sfixed64" | "double":
                field_size += 8
                return (f"if self.{self.writer_field_name} != {default_value}:\n"
                        f"    res += {field_size}")
            case _:
                return (f"if self.{self.writer_field_name} != {default_value}:\n"
                        f"    res += {field_size} + {SCALAR_SIZE_FN[self.field_type]}(self.{self.writer_field_name})")

    def create_writer(self) -> str:
        """
        Generate serialization code.
        Only writes field if value differs from default.
        """
        default_value = self.custom_default if self.custom_default is not None else self.type_default
        size_tag = sizes.generate_tag_bytes(self.wire_index, WIRE_TYPES[self.field_type])
        if self.python_type == "bool":
            if default_value == "True":
                return (f"if not self.{self.writer_field_name}:\n"
                        f"    target.{self.write_func_name}({size_tag}, self.{self.writer_field_name})")
            else:
                return (f"if self.{self.writer_field_name}:\n"
                        f"    target.{self.write_func_name}({size_tag}, self.{self.writer_field_name})")
        else:
            return (f"if self.{self.writer_field_name} != {default_value}:\n"
                    f"    target.{self.write_func_name}({size_tag}, self.{self.writer_field_name})")

    def create_reader_struct_field(self) -> str:
        """Generate reader struct field declaration with appropriate default"""
        default_value = self.custom_default if self.custom_default is not None else self.type_default
        return f"self.{self.reader_field_name}: {self.python_type} = {default_value}"

    def create_reader_case(self) -> str:
        """
        Generate deserialization case statement.
        Reads scalar value and updates the field directly.
        """
        return (f"    case {self.wire_index}:\n"
                f"        result = self._buf.{self.read_func_name}(offset)\n"
                f"        offset += result.size\n"
                f"        self.{self.reader_field_name} = result.value")

    def create_reader_method(self) -> str:
        """
        Generate getter method for the field.
        Simply returns the stored value as defaults are handled at initialization.
        """
        return (f"def {self.reader_method_name}(self) -> {self.python_type}:\n"
                f"    return self.{self.reader_field_name}")