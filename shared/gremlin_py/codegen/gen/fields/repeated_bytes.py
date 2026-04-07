# //! This module handles the generation of Python code for repeated bytes and string fields
# //! in Protocol Buffers. Repeated fields can appear zero or more times in a message.
# //! Each value in a repeated bytes/string field is length-delimited in the wire format.
# //! The module supports null values in the writer interface while preserving a clean reader API.

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

from typing import Set

from . import naming
from . import sizes

class PythonRepeatedBytesField:
    """
    Represents a repeated bytes/string field in Protocol Buffers.
    Handles both serialization and deserialization of repeated length-delimited fields.
    """

    def __init__(
        self,
        field_name: str,
        field_index: int,
        names: Set[str],
        writer_struct_name: str,
        reader_struct_name: str,
        is_string: bool = False,
    ):
        # Generate field name for the writer struct
        name = naming.struct_field_name(field_name, names)

        # Generate reader method name
        reader_prefixed = f"get_{field_name}"
        reader_method_name = naming.struct_method_name(reader_prefixed, names)

        self.writer_field_name = name
        self.reader_field_name = f"_{name}"
        self.reader_method_name = reader_method_name
        self.wire_index = field_index
        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name
        self.is_string = is_string

    def create_writer_struct_field(self) -> str:
        """
        Generate writer struct field declaration.
        Uses double optional to support explicit null values in the array.
        """
        return f"{self.writer_field_name}: typing.Optional[list[typing.Optional[bytes]]] = None"

    def create_size_check(self) -> str:
        """
        Generate size calculation code for serialization.
        Each value requires wire number, length prefix, and content size.
        """
        wire_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.BYTES)
        return (
            f"if self.{self.writer_field_name}:\n"
            f"    for v in self.{self.writer_field_name}:\n"
            f"        res += {wire_size}\n"
            f"        if v is not None:\n"
            f"            res += (((len(v) | 1).bit_length() + 6) // 7) + len(v)\n"
            f"        else:\n"
            f"            res += 1"
        )

    def create_writer(self) -> str:
        """
        Generate serialization code.
        Handles both present values and explicit nulls in the array.
        """

        bytes_tag = sizes.generate_tag_bytes(self.wire_index, sizes.ProtoWireType.BYTES)

        if self.is_string:
            write_expr = f"target.append_bytes({bytes_tag}, v.encode('utf-8'))"
        else:
            write_expr = f"target.append_bytes({bytes_tag}, v)"

        return (
            f"if self.{self.writer_field_name}:\n"
            f"    for v in self.{self.writer_field_name}:\n"
            f"        if v is not None:\n"
            f"            {write_expr}\n"
            f"        else:\n"
            f"            target.append_bytes_size_with_tag({bytes_tag}, 0)"
        )

    def create_reader_struct_field(self) -> str:
        """
        Generate reader struct field declaration.
        Uses a list to collect values during deserialization.
        """
        if self.is_string:
            return f"self.{self.reader_field_name}: typing.Optional[list[str]] = None"
        return f"self.{self.reader_field_name}: typing.Optional[list[memoryview]] = None"

    def create_reader_case(self) -> str:
        """
        Generate deserialization case statement.
        Creates list on first element and appends subsequent values.
        """
        if self.is_string:
            value_expr = "result.value.tobytes().decode('utf-8')"
        else:
            value_expr = "result.value"

        return (
            f"    case {self.wire_index}:\n"
            f"        result =  self._buf.read_bytes_view(offset)\n"
            f"        offset += result.size\n"
            f"        if self.{self.reader_field_name} is None:\n"
            f"            self.{self.reader_field_name} = []\n"
            f"        self.{self.reader_field_name}.append({value_expr})"
        )

    def create_reader_method(self) -> str:
        """
        Generate getter method that returns the array of values.
        Returns empty array if field is not present.
        """
        if self.is_string:
            return (
                f"def {self.reader_method_name}(self) -> list[str]:\n"
                f"    return self.{self.reader_field_name} if self.{self.reader_field_name} is not None else []"
            )
        else:
            if self.is_string:
                return (
                    f"def {self.reader_method_name}(self) -> list[str]:\n"
                    f"    return self.{self.reader_field_name} if self.{self.reader_field_name} is not None else []"
                )
            else:
                return (
                    f"def {self.reader_method_name}(self) -> list[memoryview]:\n"
                    f"    return self.{self.reader_field_name} if self.{self.reader_field_name} is not None else []"
                )