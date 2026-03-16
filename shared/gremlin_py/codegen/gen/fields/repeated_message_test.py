import unittest

from ... import parser
from .repeated_message import PythonRepeatedMessageField


class TestPythonRepeatedMessageField(unittest.TestCase):
    def setUp(self):
        scoped_name = parser.ScopedName("")
        buf = parser.ParserBuffer("repeated SubMessage messages = 1;")
        field = parser.fields.NormalField.parse(scoped_name, buf)

        names = set()
        self.field = PythonRepeatedMessageField(
            field.f_name,
            field.f_type,
            field.index,
            names,
            "TestWriter",
            "TestReader",
        )
        self.field.resolve("messages.SubMessage", "messages.SubMessageReader")

    def test_create_writer_struct_field(self):
        self.field.create_writer_struct_field()

    def test_create_size_check(self):
        self.field.create_size_check()

    def test_create_writer(self):
        self.field.create_writer()

    def test_create_reader_struct_field(self):
        self.field.create_reader_struct_field()

    def test_create_reader_case(self):
        self.field.create_reader_case()

    def test_create_reader_method(self):
        self.field.create_reader_method()

if __name__ == "__main__":
    unittest.main()