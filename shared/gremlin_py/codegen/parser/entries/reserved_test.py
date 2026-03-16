import unittest
from .buffer import ParserBuffer
from .reserved import Reserved, _parse_field_name

class TestReserved(unittest.TestCase):

    def test_parse_field_name(self):
        # Test case 1: Double quoted field name
        buf = ParserBuffer('"test"')
        res = _parse_field_name(buf)
        self.assertEqual("test", res)

        # Test case 2: Single quoted field name
        buf = ParserBuffer("'test'")
        res = _parse_field_name(buf)
        self.assertEqual("test", res)

    def test_parse_reserved(self):
        # Test case 1: Reserved field numbers with range
        buf = ParserBuffer("reserved 2, 15, 9 to 11;")
        res = Reserved.parse(buf)
        self.assertIsNotNone(res)
        self.assertEqual(3, len(res.items))
        self.assertEqual("2", res.items[0])
        self.assertEqual("15", res.items[1])
        self.assertEqual("9 to 11", res.items[2])

        # Test case 2: Reserved field names
        buf = ParserBuffer('reserved "foo", "bar";')
        res = Reserved.parse(buf)
        self.assertIsNotNone(res)
        self.assertEqual(2, len(res.items))
        self.assertEqual("foo", res.items[0])
        self.assertEqual("bar", res.items[1])

    def test_single_reserved(self):
        # Test single field number reservation
        buf = ParserBuffer("reserved 1;")
        res = Reserved.parse(buf)
        self.assertIsNotNone(res)
        self.assertEqual(1, len(res.items))
        self.assertEqual("1", res.items[0])

if __name__ == '__main__':
    unittest.main()