import unittest
from typing import Set

from ... import parser
from .map import PythonMapField

class TestPythonMapField(unittest.TestCase):

    def test_string_int_map(self):
        buf = parser.ParserBuffer("map<string, int32> my_map = 1;")
        scope = parser.ScopedName("")
        f = parser.fields.MessageMapField.parse(scope, buf)

        names: Set[str] = set()
        py_field = PythonMapField(
            f,
            names,
            "TestWriter",
            "TestReader",
        )

        # Mocking resolution
        py_field.resolve_message_value("path.to.MessageWriter", "path.to.MessageReader")
        py_field.resolve_enum_value("path.to.Enum")

        py_field.create_writer_struct_field()
        py_field.create_size_check()
        py_field.create_writer()
        py_field.create_reader_struct_field()
        py_field.create_reader_case()
        py_field.create_reader_method()


if __name__ == '__main__':
    unittest.main()