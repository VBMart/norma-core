import unittest
from typing import Set

from ... import parser
from .bytes import PythonBytesField

class TestPythonBytesField(unittest.TestCase):

    def test_basic_bytes_field(self):
        buf = parser.ParserBuffer("bytes data_field = 1;")
        scope = parser.ScopedName("")
        f = parser.fields.NormalField.parse(scope, buf)

        names: Set[str] = set()
        py_field = PythonBytesField(
            f.f_name,
            f.options,
            f.index,
            names,
            "TestWriter",
            "TestReader",
        )

        # Test writer field
        py_field.create_writer_struct_field()

        # Test size check
        py_field.create_size_check()

        # Test writer
        py_field.create_writer()

        # Test reader field
        py_field.create_reader_struct_field()

        # Test reader case
        py_field.create_reader_case()

        # Test reader method
        py_field.create_reader_method()

    def test_bytes_field_with_default(self):
        buf = parser.ParserBuffer("bytes data_field = 1 [default=\"hello\"];")
        scope = parser.ScopedName("")
        f = parser.fields.NormalField.parse(scope, buf)

        names: Set[str] = set()
        py_field = PythonBytesField(
            f.f_name,
            f.options,
            f.index,
            names,
            "TestWriter",
            "TestReader",
        )

        # Test reader field with default
        py_field.create_reader_struct_field()

        # Test reader method with default
        py_field.create_reader_method()

        # Test size check with default
        py_field.create_size_check()

        # Test writer with default
        py_field.create_writer()

if __name__ == '__main__':
    unittest.main()