import unittest
from typing import Set

from ... import parser
from .repeated_scalar import PythonRepeatedScalarField


class TestPythonRepeatedScalarField(unittest.TestCase):

    def test_basic_field(self):
        buf = parser.ParserBuffer("repeated int32 number_field = 1;")
        scope = parser.ScopedName("")
        f = parser.fields.NormalField.parse(scope, buf)

        names: Set[str] = set()
        py_field = PythonRepeatedScalarField(
            f.f_name,
            f.f_type.src,
            f.options,
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