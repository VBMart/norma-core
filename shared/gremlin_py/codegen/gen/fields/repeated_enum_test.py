import unittest
from ... import parser
from .repeated_enum import PythonRepeatedEnumField

class TestPythonRepeatedEnumField(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_basic_repeatable_enum_field(self):
        buf = parser.ParserBuffer("repeated TestEnum enum_field = 1;")
        scope = parser.ScopedName("")
        field = parser.fields.NormalField.parse(scope, buf)

        names = set()
        py_field = PythonRepeatedEnumField(
            field.f_name,
            field.f_type,
            field.index,
            names,
            "TestWriter",
            "TestReader",
        )
        py_field.resolve("messages.TestEnum")

        # Test wire constant
        py_field.create_writer_struct_field()
        py_field.create_size_check()
        py_field.create_writer()
        py_field.create_reader_struct_field()
        py_field.create_reader_case()
        py_field.create_reader_method()

if __name__ == '__main__':
    unittest.main()