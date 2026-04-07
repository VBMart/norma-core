#
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


from ... import parser
from . import naming
from . import sizes

class PythonRepeatedMessageField:
    """
    Represents a repeated message field in Protocol Buffers.
    Handles serialization and deserialization of repeated nested messages,
    with support for null values and lazy parsing.
    """

    target_type: parser.FieldType
    resolved_writer_type: str | None = None
    resolved_reader_type: str | None = None

    writer_field_name: str
    reader_field_name: str
    reader_method_name: str

    wire_index: int

    def __init__(
        self,
        field_name: str,
        field_type: parser.FieldType,
        field_index: int,
        names: list[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ):
        self.target_type = field_type
        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name

        name = naming.struct_field_name(field_name, names)
        self.writer_field_name = name
        self.reader_field_name = f"_{name}_bufs"

        self.wire_index = field_index

        reader_prefixed = f"get_{field_name}"
        self.reader_method_name = naming.struct_method_name(reader_prefixed, names)

    def resolve(self, resolved_writer_type: str, resolved_reader_type: str):
        """Set the resolved message type names after type resolution phase"""
        self.resolved_writer_type = resolved_writer_type
        self.resolved_reader_type = resolved_reader_type

    def create_writer_struct_field(self) -> str:
        """
        Generate writer struct field declaration.
        Uses double optional to support explicit null values in the array.
        """
        return f"{self.writer_field_name}: list[{self.resolved_writer_type} | None] | None = None"

    def create_size_check(self) -> str:
        """
        Generate size calculation code for serialization.
        Each message requires wire number, length prefix, and its own serialized size.
        """
        wire_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.BYTES)
        return f"""if self.{self.writer_field_name} is not None:
    for v in self.{self.writer_field_name}:
        res += {wire_size}
        if v is not None:
            size = v.calc_protobuf_size()
            res += (((size | 1).bit_length() + 6) // 7) + size
        else:
            res += 1
"""

    def create_writer(self) -> str:
        """
        Generate serialization code.
        Handles both present messages and explicit nulls in the array.
        """
        bytes_tag = sizes.generate_tag_bytes(self.wire_index, sizes.ProtoWireType.BYTES)
        return f"""if self.{self.writer_field_name} is not None:
    for v in self.{self.writer_field_name}:
        if v is not None:
            size = v.calc_protobuf_size()
            target.append_bytes_size_with_tag({bytes_tag}, size)
            v.encode_to(target)
        else:
            target.append_bytes_size_with_tag({bytes_tag}, 0)
"""

    def create_reader_struct_field(self) -> str:
        """
        Generate reader struct field declaration.
        Uses list to store raw message buffers until access.
        """
        return f"self.{self.reader_field_name}: list[memoryview] | None = None"

    def create_reader_case(self) -> str:
        """
        Generate deserialization case statement.
        Collects raw message buffers for later parsing.
        """
        return f"""    case {self.wire_index}:
        result = self._buf.read_bytes_view(offset)
        offset += result.size
        if self.{self.reader_field_name} is None:
            self.{self.reader_field_name} = []
        self.{self.reader_field_name}.append(result.value)
"""

    def create_reader_method(self) -> str:
        """
        Generate getter method that parses raw buffers into message instances.
        Implements lazy parsing - messages are only deserialized when accessed.
        """
        return f"""def {self.reader_method_name}(self) -> list[{self.resolved_reader_type}]:
    if self.{self.reader_field_name} is not None:
        result: list[{self.resolved_reader_type}] = []
        for buf in self.{self.reader_field_name}:
            result.append({self.resolved_reader_type}(buf))
        return result
    return []
"""