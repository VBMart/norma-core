import unittest
from typing import Set

from ... import parser
from .repeated_bytes import PythonRepeatedBytesField

class TestPythonRepeatedBytesField(unittest.TestCase):

    def test_repeatable_bytes_field_with_null_values(self):
        buf = parser.ParserBuffer("repeated bytes data_field = 1;")
        scope = parser.ScopedName("")
        f = parser.fields.NormalField.parse(scope, buf)

        names: Set[str] = set()
        py_field = PythonRepeatedBytesField(
            f.f_name,
            f.index,
            names,
            "TestWriter",
            "TestReader",
        )

        # Test wire constant
        py_field.create_writer_struct_field()
        py_field.create_size_check()
        py_field.create_writer()
        py_field.create_reader_struct_field()
        py_field.create_reader_case()
        py_field.create_reader_method()

if __name__ == '__main__':
    unittest.main()