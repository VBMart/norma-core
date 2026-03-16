import unittest
from .buffer import ParserBuffer
from .enum import Enum, EnumField

class TestEnum(unittest.TestCase):

    def test_parse_basic_enum_field(self):
        buf = ParserBuffer("UNKNOWN = 0;")
        result = EnumField.parse(buf)
        self.assertIsNotNone(result)
        self.assertEqual(0, result.start)
        self.assertEqual(12, result.end)
        self.assertEqual("UNKNOWN", result.name)
        self.assertEqual(0, result.index)

    def test_parse_enum_field_with_options(self):
        buf = ParserBuffer("EAA_RUNNING = 2 [(custom_option) = \"hello world\"];")
        result = EnumField.parse(buf)
        self.assertIsNotNone(result)
        self.assertEqual(0, result.start)
        self.assertEqual(50, result.end)
        self.assertEqual("EAA_RUNNING", result.name)
        self.assertEqual(2, result.index)
        self.assertIsNotNone(result.options)
        self.assertEqual(1, len(result.options))

    def test_parse_basic_enum(self):
        buf = ParserBuffer("enum Test { UNKNOWN = 0; OTHER = 1; }")
        result = Enum.parse(buf, None)
        self.assertIsNotNone(result)
        self.assertEqual("Test", result.name.full)
        self.assertEqual(2, len(result.fields))
        self.assertEqual("UNKNOWN", result.fields[0].name)
        self.assertEqual("OTHER", result.fields[1].name)
        self.assertEqual(0, result.fields[0].index)
        self.assertEqual(1, result.fields[1].index)

    def test_parse_empty_enum(self):
        buf = ParserBuffer("enum Test { }")
        result = Enum.parse(buf, None)
        self.assertIsNotNone(result)
        self.assertEqual("Test", result.name.full)
        self.assertEqual(0, len(result.fields))

    def test_parse_enum_with_reserved_fields(self):
        buf = ParserBuffer("""enum MonitorOptionType {
            CTA_UNKNOWN = 0;
            reserved 1;
            CTA_ENABLED = 2;
        }""")
        result = Enum.parse(buf, None)
        self.assertIsNotNone(result)
        self.assertEqual("MonitorOptionType", result.name.full)
        self.assertEqual(2, len(result.fields))
        self.assertEqual(1, len(result.reserved))
        self.assertEqual("1", result.reserved[0].items[0])

    def test_parse_enum_with_hex_values(self):
        buf = ParserBuffer("""enum TronResourceCode {
            BANDWIDTH = 0x00;
            ENERGY = 0x01;
            POWER = 0x02;
        }""")
        result = Enum.parse(buf, None)
        self.assertIsNotNone(result)
        self.assertEqual("TronResourceCode", result.name.full)
        self.assertEqual(3, len(result.fields))
        self.assertEqual(0, result.fields[0].index)
        self.assertEqual(1, result.fields[1].index)
        self.assertEqual(2, result.fields[2].index)

if __name__ == '__main__':
    unittest.main()