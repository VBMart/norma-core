# //! This module handles the generation of Python code for Protocol Buffer message fields.
# //! Message fields are nested Protocol Buffer messages that are serialized as length-delimited
# //! fields in the wire format. The module provides functionality to create reader and writer
# //! methods, handle nested message serialization, and manage wire format encoding.

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
from . import sizes

class PythonMessageField:
    """
    Represents a Protocol Buffer message field in Python.
    Message fields require special handling since they involve nested serialization
    and separate reader/writer types for efficient memory management.
    """

    def __init__(
        self,
        field_name: str,
        field_type: parser.FieldType,
        field_index: int,
        names: Set[str],
        writer_struct_name: str,
        reader_struct_name: str,
    ):
        # Generate the field name for the writer struct
        name = naming.struct_field_name(field_name, names)

        # Generate reader method name
        reader_prefixed = f"get_{field_name}"
        reader_method_name = naming.struct_method_name(reader_prefixed, names)

        self.target_type = field_type
        self.writer_field_name = name
        self.reader_field_name = f"_{name}_buf"
        self.reader_method_name = reader_method_name
        self.wire_index = field_index
        self.writer_struct_name = writer_struct_name
        self.reader_struct_name = reader_struct_name
        self.resolved_writer_type: Optional[str] = None
        self.resolved_reader_type: Optional[str] = None

    def resolve(self, resolved_writer_type: str, resolved_reader_type: str):
        """Set the resolved message type names after type resolution phase"""
        self.resolved_writer_type = resolved_writer_type
        self.resolved_reader_type = resolved_reader_type

    def create_writer_struct_field(self) -> str:
        """
        Generate writer struct field declaration.
        Message fields are optional and use their specific writer type.
        """
        if not self.resolved_writer_type:
            raise Exception(f"Writer type for field '{self.writer_field_name}' is not resolved.")
        return f"{self.writer_field_name}: typing.Optional[{self.resolved_writer_type}] = None"

    def create_size_check(self) -> str:
        """
        Generate size calculation code for serialization.
        Message fields are length-delimited, requiring size of both the message and the length prefix.
        """
        field_size = sizes.size_field_tag(self.wire_index, sizes.ProtoWireType.BYTES)
        return (
            f"if self.{self.writer_field_name} is not None:\n"
            f"    size = self.{self.writer_field_name}.calc_protobuf_size()\n"
            f"    if size > 0:\n"
            f"        res += {field_size} + (((size | 1).bit_length() + 6) // 7) + size"
        )

    def create_writer(self) -> str:
        """
        Generate serialization code.
        Writes the field tag, length prefix, and then recursively serializes the nested message.
        """
        bytes_tag = sizes.generate_tag_bytes(self.wire_index, sizes.ProtoWireType.BYTES)

        return (
            f"if self.{self.writer_field_name} is not None:\n"
            f"    size = self.{self.writer_field_name}.calc_protobuf_size()\n"
            f"    if size > 0:\n"
            f"        target.append_bytes_size_with_tag({bytes_tag}, size)\n"
            f"        self.{self.writer_field_name}.encode_to(target)"
        )

    def create_reader_struct_field(self) -> str:
        """
        Generate reader struct field declaration.
        Reader stores the raw bytes until lazy deserialization is needed.
        """
        return f"self.{self.reader_field_name}: typing.Optional[memoryview] = None"

    def create_reader_case(self) -> str:
        """
        Generate deserialization case statement.
        Stores the raw message bytes for later processing.
        """
        return (
            f"    case {self.wire_index}:\n"
            f"        result = self._buf.read_bytes_view(offset)\n"
            f"        offset += result.size\n"
            f"        self.{self.reader_field_name} = result.value"
        )

    def create_reader_method(self) -> str:
        """
        Generate getter method that creates reader instance from stored bytes.
        This implements lazy deserialization - messages are only parsed when accessed.
        """
        if not self.resolved_reader_type:
            raise Exception(f"Reader type for field '{self.writer_field_name}' is not resolved.")
        return (
            f"def {self.reader_method_name}(self) -> {self.resolved_reader_type}:\n"
            f"    if self.{self.reader_field_name} is not None:\n"
            f"        return {self.resolved_reader_type}(self.{self.reader_field_name})\n"
            f"    return {self.resolved_reader_type}(b'')"
        )