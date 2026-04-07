import unittest
from ... import parser
from .enum import PythonEnumField


class TestPythonEnumField(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_basic_enum_field(self):
        buf = parser.ParserBuffer("TestEnum enum_field = 1;")
        scope = parser.ScopedName("")
        field = parser.fields.NormalField.parse(scope, buf)

        names = set()
        py_field = PythonEnumField(
            field.f_name,
            field.f_type,
            field.options,
            field.index,
            names,
            "TestWriter",
            "TestReader",
        )
        py_field.resolve("messages.TestEnum")

        py_field.create_writer_struct_field()
        py_field.create_size_check()
        py_field.create_writer()
        py_field.create_reader_struct_field()
        py_field.create_reader_case()
        py_field.create_reader_method()

    def test_enum_field_with_default(self):
        buf = parser.ParserBuffer("TestEnum enum_field = 1 [default = OTHER];")
        scope = parser.ScopedName("")
        field = parser.fields.NormalField.parse(scope, buf)

        names = set()
        py_field = PythonEnumField(
            field.f_name,
            field.f_type,
            field.options,
            field.index,
            names,
            "TestWriter",
            "TestReader",
        )
        py_field.resolve("messages.TestEnum")

        py_field.create_writer_struct_field()
        py_field.create_size_check()
        py_field.create_writer()
        py_field.create_reader_struct_field()
        py_field.create_reader_case()
        py_field.create_reader_method()

if __name__ == '__main__':
    unittest.main()