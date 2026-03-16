import unittest
from .buffer import ParserBuffer
from .scoped_name import ScopedName
from .field_type import FieldType

class TestFieldType(unittest.TestCase):

    def test_field_type_parsing_scalar_types(self):
        buf = ParserBuffer("int32")
        scope = ScopedName("test")
        field_type = FieldType.parse(scope, buf)
        self.assertTrue(field_type.is_scalar)
        self.assertFalse(field_type.is_bytes)
        self.assertIsNone(field_type.name)

    def test_field_type_parsing_bytes_types(self):
        buf = ParserBuffer("bytes")
        scope = ScopedName("test")
        field_type = FieldType.parse(scope, buf)
        self.assertFalse(field_type.is_scalar)
        self.assertTrue(field_type.is_bytes)
        self.assertIsNone(field_type.name)

    def test_field_type_parsing_message_types(self):
        buf = ParserBuffer("MyMessage")
        scope = ScopedName("test")
        field_type = FieldType.parse(scope, buf)
        self.assertFalse(field_type.is_scalar)
        self.assertFalse(field_type.is_bytes)
        self.assertIsNotNone(field_type.name)

if __name__ == '__main__':
    unittest.main()