# //! This module handles the generation of Python code for Protocol Buffer map fields.
# //! Protocol Buffers represent maps as repeated key-value pairs in the wire format.
# //! In Python, maps are implemented using dictionaries.

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

from typing import Optional, Set

from ... import parser
from . import naming
from . import scalar
from . import sizes

class PythonMapField:
    """
    Represents a Protocol Buffer map field in Python.
    Maps are encoded as repeated messages where each message contains a key and value field.
    """

    def __init__(
        self,
        field: parser.fields.MessageMapField,
        names: Set[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ):
        # Generate field names
        name = naming.struct_field_name(field.f_name, names)

        # Generate reader method name
        reader_prefixed = f"get_{field.f_name}"
        reader_method_name = naming.struct_method_name(reader_prefixed, names)

        self.key_type = field.key_type
        self.value_type = field.value_type
        self.wire_index = field.index
        self.writer_field_name = name
        self.reader_field_name = f"_{name}"
        self.reader_method_name = reader_method_name
        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name

        self.resolved_enum_type: Optional[str] = None
        self.resolved_writer_message_type: Optional[str] = None
        self.resolved_reader_message_type: Optional[str] = None

    # Key-related helper functions

    def _key_type(self) -> str:
        if self.key_type in ["string", "bytes"]:
            return "str" if self.key_type == "string" else "bytes"
        return scalar.SCALAR_PYTHON_TYPE[self.key_type]

    def _key_size(self) -> str:
        match self.key_type:
            case "fixed32" | "sfixed32" | "float":
                return "4"
            case "fixed64" | "sfixed64" | "double":
                return "8"
            case "bool":
                return "1"
            case "string" | "bytes":
                return "gremlin.sizes.size_bytes(key)"
            case _:
                return f"{scalar.SCALAR_SIZE_FN[self.key_type]}(key)"

    def _key_write(self) -> str:
        if self.key_type in ["string", "bytes"]:
            key_bytes_tag = sizes.generate_tag_bytes(1, sizes.ProtoWireType.BYTES)
            return f"target.append_bytes({key_bytes_tag}, key)"
        
        key_scalar_tag = sizes.generate_tag_bytes(1, scalar.WIRE_TYPES[self.key_type])
        return f"target.{scalar.SCALAR_WRITER_FN[self.key_type]}({key_scalar_tag}, key)"

    def _key_read(self) -> str:
        indent = "\n" + " " * 20
        lines = []
        if self.key_type in ["string", "bytes"]:
            lines.append("key_res = entry_buf.read_bytes_view(offset)")
            if self.key_type == "string":
                lines.append("key = key_res.value.tobytes().decode('utf-8')")
            else:
                lines.append("key = key_res.value.tobytes()")
        else:
            lines.append(f"key_res = entry_buf.{scalar.SCALAR_READER_FN[self.key_type]}(offset)")
            lines.append("key = key_res.value")
        lines.append("offset += key_res.size")
        return indent.join(lines)

    # Value-related helper functions

    def _value_type(self) -> str:
        if self.value_type.is_bytes:
            if self.value_type.src == "string":
                return "str"
            return "bytes"
        elif self.value_type.is_scalar:
            return scalar.SCALAR_PYTHON_TYPE[self.value_type.src]
        elif self.value_type.is_enum:
            return self.resolved_enum_type
        else:
            return self.resolved_writer_message_type

    def _value_reader_type(self) -> str:
        if self.value_type.is_bytes:
            if self.value_type.src == "string":
                return "str"
            return "memoryview"
        elif self.value_type.is_scalar:
            return scalar.SCALAR_PYTHON_TYPE[self.value_type.src]
        elif self.value_type.is_enum:
            return self.resolved_enum_type
        else:
            return self.resolved_reader_message_type

    def _value_read(self) -> str:
        indent = "\n" + " " * 20
        lines = []
        if self.value_type.is_bytes:
            lines.append("value_res = entry_buf.read_bytes_view(offset)")
            if self.value_type.src == "string":
                lines.append("value = value_res.value.tobytes().decode('utf-8')")
            else:
                lines.append("value = value_res.value")
            lines.append("offset += value_res.size")
        elif self.value_type.is_scalar:
            lines.append(f"value_res = entry_buf.{scalar.SCALAR_READER_FN[self.value_type.src]}(offset)")
            lines.append("value = value_res.value")
            lines.append("offset += value_res.size")
        elif self.value_type.is_enum:
            lines.append("value_res = entry_buf.read_int32(offset)")
            lines.append(f"value = {self.resolved_enum_type}(value_res.value)")
            lines.append("offset += value_res.size")
        else:
            lines.append("value_res = entry_buf.read_bytes_view(offset)")
            lines.append(f"value = {self.resolved_reader_message_type}(value_res.value)")
            lines.append("offset += value_res.size")
        return indent.join(lines)

    def _value_size(self) -> str:
        if self.value_type.is_bytes:
            return "gremlin.sizes.size_bytes(value)"
        elif self.value_type.is_scalar:
            match self.value_type.src:
                case "fixed32" | "sfixed32" | "float":
                    return "4"
                case "fixed64" | "sfixed64" | "double":
                    return "8"
                case "bool":
                    return "1"
                case _:
                    return f"{scalar.SCALAR_SIZE_FN[self.value_type.src]}(value)"
        elif self.value_type.is_enum:
            return "((value.value | 1).bit_length() + 6) // 7"
        else:
            return "value.calc_protobuf_size()"

    def _value_write(self) -> str:
        if self.value_type.is_bytes:
            value_bytes_tag = sizes.generate_tag_bytes(2, sizes.ProtoWireType.BYTES)
            return f"target.append_bytes({value_bytes_tag}, value)"
        elif self.value_type.is_scalar:
            value_scalar_tag = sizes.generate_tag_bytes(2, scalar.WIRE_TYPES[self.value_type.src])
            return f"target.{scalar.SCALAR_WRITER_FN[self.value_type.src]}({value_scalar_tag}, value)"
        elif self.value_type.is_enum:
            value_enum_tag = sizes.generate_tag_bytes(2, sizes.ProtoWireType.VARINT)
            return f"target.append_int32({value_enum_tag}, value.value)"
        else:
            return "value.encode_to(target)"

    def _value_reader_var(self) -> str:
        if self.value_type.is_bytes:
            return "value: bytes = b''"
        elif self.value_type.is_scalar:
            return f"value: {scalar.SCALAR_PYTHON_TYPE[self.value_type.src]} = {scalar.SCALAR_DEFAULT_VALUE[self.value_type.src]}"
        elif self.value_type.is_enum:
            return f"value: {self.resolved_enum_type} = {self.resolved_enum_type}(0)"
        else:
            return f"value: typing.Optional[{self.resolved_reader_message_type}] = None"

    # Type resolution methods

    def resolve_enum_value(self, resolved_enum_type: str):
        self.resolved_enum_type = resolved_enum_type

    def resolve_message_value(self, resolved_writer_message_type: str, resolved_reader_message_type: str):
        self.resolved_writer_message_type = resolved_writer_message_type
        self.resolved_reader_message_type = resolved_reader_message_type

    # Code generation methods

    def create_writer_struct_field(self) -> str:
        key_type = self._key_type()
        value_type = self._value_type()
        return f"{self.writer_field_name}: typing.Optional[dict[{key_type}, {value_type}]] = None"

    def create_size_check(self) -> str:
        key_size_code = self._key_size()
        value_size_code = self._value_size()
        key_is_ld = self.key_type in ["string", "bytes"]
        value_is_ld = self.value_type.is_bytes or (not self.value_type.is_scalar and not self.value_type.is_enum)

        add_key_len_size = "entry_size += ((key_size | 1).bit_length() + 6) // 7" if key_is_ld else ""
        add_value_len_size = "entry_size += ((value_size | 1).bit_length() + 6) // 7" if value_is_ld else ""

        key_tag_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)
        value_tag_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)
        map_entry_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.BYTES)

        return f"""
if self.{self.writer_field_name}:
    entry_wire_size = {map_entry_size}
    for key, value in self.{self.writer_field_name}.items():
        key_size = {key_size_code}
        value_size = {value_size_code}
        entry_size = key_size + value_size + {key_tag_size} + {value_tag_size}
        {add_key_len_size}
        {add_value_len_size}
        res += entry_wire_size + ((entry_size | 1).bit_length() + 6) // 7 + entry_size
"""

    def create_writer(self) -> str:
        key_write_code = self._key_write()
        key_size_code = self._key_size()
        value_size_code = self._value_size()
        key_is_ld = self.key_type in ["string", "bytes"]
        value_is_ld = self.value_type.is_bytes or (not self.value_type.is_scalar and not self.value_type.is_enum)

        add_key_len_size = "entry_size += ((key_size | 1).bit_length() + 6) // 7" if key_is_ld else ""
        add_value_len_size = "entry_size += ((value_size | 1).bit_length() + 6) // 7" if value_is_ld else ""

        value_writer_final = ""
        if self.value_type.is_bytes or self.value_type.is_scalar or self.value_type.is_enum:
            value_writer_final = self._value_write()
        else:  # message
            value_writer_final = f"target.append_bytes_tag(2, value_size)\n        {self._value_write()}"

        tag_1_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)
        tag_2_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.VARINT)

        return f"""
if self.{self.writer_field_name}:
    for key, value in self.{self.writer_field_name}.items():
        key_size = {key_size_code}
        value_size = {value_size_code}
        entry_size = key_size + value_size + {tag_1_size} + {tag_2_size}
        {add_key_len_size}
        {add_value_len_size}
        target.append_bytes_tag({self.wire_index}, entry_size)
        {key_write_code}
        {value_writer_final}
"""

    def create_reader_struct_field(self) -> str:
        return f"self.{self.reader_field_name}: typing.Optional[list[bytes]] = None"

    def create_reader_case(self) -> str:
        return f"""
    case {self.wire_index}:
        result = self._buf.read_bytes_view(offset)
        offset += result.size
        if self.{self.reader_field_name} is None:
            self.{self.reader_field_name} = []
        self.{self.reader_field_name}.append(result.value)
"""

    def create_reader_method(self) -> str:
        key_type = self._key_type()
        value_reader_type = self._value_reader_type()
        key_read_code = self._key_read()
        value_reader_var_code = self._value_reader_var()
        value_read_code = self._value_read()

        return_type = f"typing.Optional[dict[{key_type}, {value_reader_type}]]"

        return f"""
def {self.reader_method_name}(self) -> {return_type}:
    if self.{self.reader_field_name}:
        result: dict[{key_type}, {value_reader_type}] = {{}}
        for buf_item in self.{self.reader_field_name}:
            entry_buf = gremlin.Reader(buf_item)
            offset = 0
            key: typing.Optional[{key_type}] = None
            has_key = False
            {value_reader_var_code}
            has_value = False

            while entry_buf.has_next(offset):
                tag = entry_buf.read_tag_at(offset)
                offset += tag.size
                if tag.number == 1:
                    {key_read_code}
                    has_key = True
                elif tag.number == 2:
                    {value_read_code}
                    has_value = True
                else:
                    offset = entry_buf.skip_data(offset, tag.wire)
            
            if has_key and has_value:
                result[key] = value
        return result
    return None
"""