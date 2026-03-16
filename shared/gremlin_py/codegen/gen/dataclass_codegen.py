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

"""
Provides functionality for generating Python code from Protocol Buffer dataclass definitions.
This module handles the generation of wire format enums, writer dataclasses, and reader classes,
including all necessary fields, methods, and nested types.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from .output import FileOutput

if TYPE_CHECKING:
    from .dataclass import PythonDataclass


class CodeGenerator:
    """
    Handles the generation of Python source code for Protocol Buffer messages.
    Manages the creation of wire format enums, writer dataclasses, and reader classes,
    along with all their associated methods and fields.
    """

    def __init__(self, target: PythonDataclass, out_file: FileOutput):
        self.target = target
        self.out_file = out_file

    def generate(self):
        """
        Generate all code components for the dataclass.
        This includes the wire format enum, writer dataclass, and reader class.
        """
        self._generate_writer()
        self._generate_reader()


    def _generate_writer(self):
        """Generate the writer dataclass that handles serialization."""
        self.out_file.write_string("@dataclasses.dataclass")
        self.out_file.write_string(f"class {self.target.writer_name}:")
        with self.out_file.indent():
            self._generate_fields()
            self._generate_size_function()
            self._generate_serialize_function()
        self.out_file.linebreak()

    def _generate_fields(self):
        """Generate field definitions for the writer dataclass."""
        if self.target.fields:
            self.out_file.write_comment("fields")
            for field in self.target.fields:
                self.out_file.write_string(field.create_writer_struct_field())
            self.out_file.linebreak()

    def _generate_reader(self):
        """Generate the reader class for deserialization."""
        self.out_file.write_string(f"class {self.target.reader_name}:")
        with self.out_file.indent():
            self._generate_reader_init()
            self._generate_reader_getters()
        self.out_file.linebreak()

    def _generate_reader_init(self):
        """Generate the initialization method for the reader."""
        self.out_file.write_string("def __init__(self, src: memoryview):")
        with self.out_file.indent():
            if not self.target.fields:
                self.out_file.write_string("pass")
                return

            for field in self.target.fields:
                self.out_file.write_string(field.create_reader_struct_field())
            self.out_file.linebreak()
            
            self.out_file.write_string("if not src:")
            with self.out_file.indent():
                self.out_file.write_string("return")
            self.out_file.write_string("self._buf = gremlin.Reader(src)")
            self.out_file.write_string("offset = 0")
            self.out_file.write_string("while offset < len(src):")
            with self.out_file.indent():
                self.out_file.write_string("tag = self._buf.read_tag_at(offset)")
                self.out_file.write_string("offset += tag.size")
                self.out_file.write_string("match tag.number:")
                
                for field in self.target.fields:
                    self.out_file.write_string(field.create_reader_case())
                
                self.out_file.write_string("    case _:")
                self.out_file.write_string("        offset = self._buf.skip_data(offset, tag.wire)")
        self.out_file.linebreak()

    def _generate_reader_getters(self):
        """Generate getter methods for reader fields."""
        for field in self.target.fields:
            self.out_file.write_string(field.create_reader_method())
            self.out_file.linebreak()

    def _generate_size_function(self):
        """Generate the size calculation function for serialization."""
        self.out_file.write_string("def calc_protobuf_size(self) -> int:")
        with self.out_file.indent():
            if not self.target.fields:
                self.out_file.write_string("return 0")
                return

            self.out_file.write_string("res = 0")
            for field in self.target.fields:
                self.out_file.write_string(field.create_size_check())
            self.out_file.write_string("return res")
        self.out_file.linebreak()

    def _generate_serialize_function(self):
        """Generate the serialization functions."""
        self.out_file.write_string("def encode(self) -> bytes:")
        with self.out_file.indent():
            self.out_file.write_string("size = self.calc_protobuf_size()")
            self.out_file.write_string("if size == 0:")
            with self.out_file.indent():
                self.out_file.write_string("return b''")
            self.out_file.write_string("buf = bytearray(size)")
            self.out_file.write_string("writer = gremlin.Writer(buf)")
            self.out_file.write_string("self.encode_to(writer)")
            self.out_file.write_string("return bytes(buf)")
        self.out_file.linebreak()

        self.out_file.write_string("def encode_to(self, target: typing.Union[gremlin.Writer, gremlin.StreamingWriter]):")
        with self.out_file.indent():
            if not self.target.fields:
                self.out_file.write_string("pass")
                return
            
            for field in self.target.fields:
                self.out_file.write_string(field.create_writer())
        self.out_file.linebreak()