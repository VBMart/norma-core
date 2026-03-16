import unittest
from .buffer import ParserBuffer
from .extension import Extensions
from .errors import ProtoError, ParsingError

class TestExtensions(unittest.TestCase):

    def test_parse_basic_extensions(self):
        buf = ParserBuffer("extensions 2, 15, 9 to 11;")
        res = Extensions.parse(buf)
        self.assertIsNotNone(res)
        self.assertEqual(3, len(res.items))
        self.assertEqual("2", res.items[0])
        self.assertEqual("15", res.items[1])
        self.assertEqual("9 to 11", res.items[2])

    def test_parse_invalid_extensions(self):
        # Missing semicolon
        with self.assertRaises(ProtoError) as cm:
            buf = ParserBuffer("extensions 2, 15")
            Extensions.parse(buf)
        self.assertEqual(cm.exception.error_code, ParsingError.SemicolonExpected)

    def test_check_field_containment(self):
        buf = ParserBuffer("extensions 2, 15, 9 to 11;")
        extensions = Extensions.parse(buf)
        self.assertIsNotNone(extensions)

        # Test single numbers
        self.assertTrue(extensions.contains_field(2))
        self.assertTrue(extensions.contains_field(15))
        self.assertFalse(extensions.contains_field(3))

        # Test range
        self.assertTrue(extensions.contains_field(9))
        self.assertTrue(extensions.contains_field(10))
        self.assertTrue(extensions.contains_field(11))
        self.assertFalse(extensions.contains_field(12))

if __name__ == '__main__':
    unittest.main()