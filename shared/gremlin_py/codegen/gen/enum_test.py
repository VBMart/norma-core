import unittest

from .. import parser
from .enum import PythonEnum


class TestPythonEnum(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_enum_generation(self):
        buf = parser.ParserBuffer(
            """enum ForeignEnum {
                FOREIGN_FOO = 0;
                FOREIGN_BAR = 1;
                FOREIGN_BAZ = 2;
            }"""
        )
        result = parser.Enum.parse(buf, None)
        self.assertIsNotNone(result)

        names = set()
        py_enum = PythonEnum(result, "", names)
        py_enum.create_enum_def()

    def test_enum_generation_with_unknown(self):
        buf = parser.ParserBuffer(
            """enum ForeignEnum {
                FOREIGN_FOO = 1;
                FOREIGN_BAR = 2;
                FOREIGN_BAZ = 3;
            }"""
        )
        result = parser.Enum.parse(buf, None)
        self.assertIsNotNone(result)

        names = set()
        py_enum = PythonEnum(result, "", names)
        py_enum.create_enum_def()


if __name__ == '__main__':
    unittest.main()