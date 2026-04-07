# //! This module handles the generation of Python code for Protocol Buffer bytes and string fields.
# //! Both field types are handled similarly as they share the same wire format representation.
# //! The module provides functionality to create reader and writer methods, handle defaults,
# //! and manage wire format encoding for both bytes and string fields.

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
from . import sizes

def _format_string_literal(s: str) -> str:
    """
    Formats a string literal for use in Python code, properly escaping special characters
    and converting to a byte string representation.
    """
    # Remove surrounding quotes from input
    cropped = s[1:-1]
    
    res = bytearray()
    res.extend(cropped.encode('utf-8'))

    return f"b'{res.hex()}'"


class PythonBytesField:
    """
    Represents a Protocol Buffer bytes/string field in Python, managing both reading and writing
    of the field along with wire format details.
    """

    def __init__(
        self,
        field_name: str,
        field_opts: Optional[List[parser.Option]],
        field_index: int,
        names: Set[str],
        writer_struct_name: str,
        reader_struct_name: str,
        is_string: bool = False
    ):
        # Generate the field name for the writer struct
        name = naming.struct_field_name(field_name, names)

        ## Generate reader method name (get_fieldname)
        reader_prefixed = f"get_{field_name}"
        reader_method_name = naming.struct_method_name(reader_prefixed, names)

        # Process field options for default value
        custom_default: Optional[str] = None
        if field_opts:
            for opt in field_opts:
                if opt.name == "default":
                    custom_default = _format_string_literal(opt.value)
                    break
        
        self.custom_default = custom_default
        self.writer_field_name = name
        self.reader_field_name = f"_{name}"
        self.reader_method_name = reader_method_name
        self.wire_index = field_index
        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name
        self.is_string = is_string

    def create_writer_struct_field(self) -> str:
        """Generate writer struct field declaration"""
        return f"{self.writer_field_name}: typing.Optional[bytes] = None"

    def create_size_check(self) -> str:
        """Generate size calculation code for serialization"""
        field_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.BYTES)
        if self.custom_default:
            # When default value exists, only include size if value differs from default
            return (f"if self.{self.writer_field_name} is not None:\n"
                    f"    if self.{self.writer_field_name} != {self.custom_default}:\n"
                    f"        bytes_len = len(self.{self.writer_field_name})\n"
                    f"        bytes_len_size = ((bytes_len | 1).bit_length() + 6) // 7\n"
                    f"        res += {field_size} + bytes_len_size + bytes_len\n"
                    f"else:\n"
                    f"    res += {field_size} + 1")
        else:
            # Without default, include size if value exists
            return (f"if self.{self.writer_field_name} is not None and len(self.{self.writer_field_name}) > 0:\n"
                    f"    bytes_len = len(self.{self.writer_field_name})\n"
                    f"    bytes_len_size = ((bytes_len | 1).bit_length() + 6) // 7\n"
                    f"    res += {field_size} + bytes_len_size + bytes_len")
        
    def create_writer(self) -> str:
        bytes_tag = sizes.generate_tag_bytes(self.wire_index, sizes.ProtoWireType.BYTES)
        """Generate serialization code"""
        if self.custom_default:
            # With default value, only write if different from default
            if self.is_string:
                write_expr = f"target.append_bytes({bytes_tag}, self.{self.writer_field_name}.encode('utf-8'))"
            else:
                write_expr = f"target.append_bytes({bytes_tag}, self.{self.writer_field_name})"

            return (f"if self.{self.writer_field_name} is not None:\n"
                    f"    if self.{self.writer_field_name} != {self.custom_default}:\n"
                    f"        {write_expr}\n"
                    f"else:\n"
                    f"    target.append_bytes({bytes_tag}, b'')")
        else:
            # Without default, write if value exists
            if self.is_string:
                write_expr = f"target.append_bytes({bytes_tag}, self.{self.writer_field_name}.encode('utf-8'))"
            else:
                write_expr = f"target.append_bytes({bytes_tag}, self.{self.writer_field_name})"
            return (f"if self.{self.writer_field_name} is not None and len(self.{self.writer_field_name}) > 0:\n"
                    f"    {write_expr}")

    def create_reader_struct_field(self) -> str:
        """Generate reader struct field declaration"""
        field_type = "str" if self.is_string else "memoryview"
        if self.custom_default:
            if self.is_string:
                return f"self.{self.reader_field_name}: typing.Optional[{field_type}] = {self.custom_default}.decode('utf-8')"
            return f"self.{self.reader_field_name}: typing.Optional[{field_type}] = {self.custom_default}"
        else:
            return f"self.{self.reader_field_name}: typing.Optional[{field_type}] = None"

    def create_reader_case(self) -> str:
        """Generate deserialization case statement"""
        if self.is_string:
            return (f"    case {self.wire_index}:\n"
                    f"        result = self._buf.read_bytes_view(offset)\n"
                    f"        offset += result.size\n"
                    f"        self.{self.reader_field_name} = result.value.tobytes().decode('utf-8')")
        return (f"    case {self.wire_index}:\n"
                f"        result = self._buf.read_bytes_view(offset)\n"
                f"        offset += result.size\n"
                f"        self.{self.reader_field_name} = result.value")

    def create_reader_method(self) -> str:
        """Generate getter method for the field"""
        if self.is_string:
            if self.custom_default:
                return f"def {self.reader_method_name}(self) -> str:\n    return self.{self.reader_field_name} if self.{self.reader_field_name} is not None else {self.custom_default}.decode('utf-8')"
            else:
                return f"def {self.reader_method_name}(self) -> str:\n    return self.{self.reader_field_name} if self.{self.reader_field_name} is not None else ''"
        else:
            if self.custom_default:
                return f"def {self.reader_method_name}(self) -> memoryview:\n    return self.{self.reader_field_name} if self.{self.reader_field_name} is not None else {self.custom_default}"
            else:
                return f"def {self.reader_method_name}(self) -> memoryview:\n    return self.{self.reader_field_name} if self.{self.reader_field_name} is not None else memoryview(b'')"