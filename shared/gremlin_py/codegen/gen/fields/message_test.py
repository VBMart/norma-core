import unittest

from ... import parser
from .message import PythonMessageField


class TestMessageField(unittest.TestCase):
    def test_basic_message_field(self):
        scope = parser.ScopedName("")
        buf = parser.ParserBuffer("SubMessage message_field = 1;")
        f = parser.fields.NormalField.parse(scope, buf)

        names = set()
        py_field = PythonMessageField(
            f.f_name,
            f.f_type,
            f.index,
            names,
            "TestWriter",
            "TestReader",
        )
        py_field.resolve("messages.SubMessage", "messages.SubMessageReader")

        py_field.create_writer_struct_field()
        py_field.create_size_check()
        py_field.create_writer()
        py_field.create_reader_struct_field()
        py_field.create_reader_case()
        py_field.create_reader_method()


if __name__ == "__main__":
    unittest.main()