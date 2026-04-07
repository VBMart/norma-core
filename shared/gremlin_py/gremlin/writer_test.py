import unittest
from .writer import Writer

class TestWriter(unittest.TestCase):

    def test_writer(self):
        buf = bytearray(100)
        writer = Writer(buf)

        # String
        writer.append_bytes(1, b"hello")
        self.assertEqual(bytes([0x0A, 0x05, 104, 101, 108, 108, 111]), bytes(buf[0:7]))
        self.assertEqual(7, writer.pos)
        writer.reset()

        # Bool
        writer.append_bool(2, True)
        writer.append_bool(3, False)
        self.assertEqual(bytes([0x10, 0x01, 0x18, 0x00]), bytes(buf[0:4]))
        self.assertEqual(4, writer.pos)
        writer.reset()

        # Int32
        writer.append_int32(4, 150)
        self.assertEqual(bytes([0x20, 0x96, 0x01]), bytes(buf[0:3]))
        self.assertEqual(3, writer.pos)
        writer.reset()

        # Int64
        writer.append_int64(5, 1500)
        self.assertEqual(bytes([0x28, 0xdc, 0x0b]), bytes(buf[0:3]))
        self.assertEqual(3, writer.pos)
        writer.reset()

        # UInt32
        writer.append_uint32(6, 150)
        self.assertEqual(bytes([0x30, 0x96, 0x01]), bytes(buf[0:3]))
        self.assertEqual(3, writer.pos)
        writer.reset()

        # UInt64
        writer.append_uint64(7, 1500)
        self.assertEqual(bytes([0x38, 0xdc, 0x0b]), bytes(buf[0:3]))
        self.assertEqual(3, writer.pos)
        writer.reset()

        # SInt32 (zigzag encoding)
        writer.append_sint32(8, -1)
        self.assertEqual(bytes([0x40, 0x01]), bytes(buf[0:2]))
        self.assertEqual(2, writer.pos)
        writer.reset()

        # SInt64 (zigzag encoding)
        writer.append_sint64(9, -1)
        self.assertEqual(bytes([0x48, 0x01]), bytes(buf[0:2]))
        self.assertEqual(2, writer.pos)
        writer.reset()

        # Fixed32
        writer.append_fixed32(10, 0x12345678)
        self.assertEqual(bytes([0x55, 0x78, 0x56, 0x34, 0x12]), bytes(buf[0:5]))
        self.assertEqual(5, writer.pos)
        writer.reset()

        # Fixed64
        writer.append_fixed64(11, 0x1234567890ABCDEF)
        self.assertEqual(bytes([0x59, 0xEF, 0xCD, 0xAB, 0x90, 0x78, 0x56, 0x34, 0x12]), bytes(buf[0:9]))
        self.assertEqual(9, writer.pos)
        writer.reset()

        # SFixed32
        writer.append_sfixed32(12, -1)
        self.assertEqual(bytes([0x65, 0xFF, 0xFF, 0xFF, 0xFF]), bytes(buf[0:5]))
        self.assertEqual(5, writer.pos)
        writer.reset()

        # SFixed64
        writer.append_sfixed64(13, -1)
        self.assertEqual(bytes([0x69, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]), bytes(buf[0:9]))
        self.assertEqual(9, writer.pos)
        writer.reset()

        # Float32
        writer.append_float32(14, 3.14)
        # Note: Python's float representation might differ slightly
        self.assertEqual(bytes([0x75, 0xC3, 0xF5, 0x48, 0x40]), bytes(buf[0:5]))
        self.assertEqual(5, writer.pos)
        writer.reset()

        # Float64
        writer.append_float64(15, 3.14)
        self.assertEqual(bytes([0x79, 0x1F, 0x85, 0xEB, 0x51, 0xB8, 0x1E, 0x09, 0x40]), bytes(buf[0:9]))
        self.assertEqual(9, writer.pos)
        writer.reset()

    def test_writer_append_string(self):
        test_cases = [
            {"name": "empty string", "tag": 1, "data": "", "want": bytes([0x0a, 0x00])},
            {"name": "hello world", "tag": 1, "data": "hello world", "want": bytes([0x0a, 0x0b, 0x68, 0x65, 0x6c, 0x6c, 0x6f, 0x20, 0x77, 0x6f, 0x72, 0x6c, 0x64])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_bytes(tc["tag"], tc["data"].encode('utf-8'))
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_int32(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x08, 0x00])},
            {"name": "positive small", "tag": 1, "data": 127, "want": bytes([0x08, 0x7f])},
            {"name": "negative small", "tag": 1, "data": -127, "want": bytes([0x08, 0x81, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x01])},
            {"name": "max int32", "tag": 1, "data": 2147483647, "want": bytes([0x08, 0xff, 0xff, 0xff, 0xff, 0x07])},
            {"name": "min int32", "tag": 1, "data": -2147483648, "want": bytes([0x08, 0x80, 0x80, 0x80, 0x80, 0xf8, 0xff, 0xff, 0xff, 0xff, 0x01])},
        ]
        buf = bytearray(64)

        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_int32(tc["tag"], tc["data"])
                self.assertEqual(bytes(tc["want"]), bytes(buf[0:writer.pos]))

    def test_writer_append_sint32(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x08, 0x00])},
            {"name": "positive small", "tag": 1, "data": 127, "want": bytes([0x08, 0xfe, 0x01])},
            {"name": "negative small", "tag": 1, "data": -127, "want": bytes([0x08, 0xfd, 0x01])},
            {"name": "max int32", "tag": 1, "data": 2147483647, "want": bytes([0x08, 0xfe, 0xff, 0xff, 0xff, 0x0f])},
            {"name": "min int32", "tag": 1, "data": -2147483648, "want": bytes([0x08, 0xff, 0xff, 0xff, 0xff, 0x0f])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_sint32(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_sint64(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x08, 0x00])},
            {"name": "positive small", "tag": 1, "data": 127, "want": bytes([0x08, 0xfe, 0x01])},
            {"name": "negative small", "tag": 1, "data": -127, "want": bytes([0x08, 0xfd, 0x01])},
            {"name": "max int64", "tag": 1, "data": 9223372036854775807, "want": bytes([0x08, 0xfe, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x01])},
            {"name": "min int64", "tag": 1, "data": -9223372036854775808, "want": bytes([0x08, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x01])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_sint64(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_sfixed32(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x0d, 0x00, 0x00, 0x00, 0x00])},
            {"name": "positive", "tag": 1, "data": 127, "want": bytes([0x0d, 0x7f, 0x00, 0x00, 0x00])},
            {"name": "negative", "tag": 1, "data": -127, "want": bytes([0x0d, 0x81, 0xff, 0xff, 0xff])},
            {"name": "max int32", "tag": 1, "data": 2147483647, "want": bytes([0x0d, 0xff, 0xff, 0xff, 0x7f])},
            {"name": "min int32", "tag": 1, "data": -2147483648, "want": bytes([0x0d, 0x00, 0x00, 0x00, 0x80])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_sfixed32(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_sfixed64(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])},
            {"name": "positive", "tag": 1, "data": 127, "want": bytes([0x09, 0x7f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])},
            {"name": "negative", "tag": 1, "data": -127, "want": bytes([0x09, 0x81, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])},
            {"name": "max int64", "tag": 1, "data": 9223372036854775807, "want": bytes([0x09, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x7f])},
            {"name": "min int64", "tag": 1, "data": -9223372036854775808, "want": bytes([0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_sfixed64(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_int64(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x08, 0x00])},
            {"name": "positive small", "tag": 1, "data": 127, "want": bytes([0x08, 0x7f])},
            {"name": "negative small", "tag": 1, "data": -127, "want": bytes([0x08, 0x81, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x01])},
            {"name": "max int64", "tag": 1, "data": 9223372036854775807, "want": bytes([0x08, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x7f])},
            {"name": "min int64", "tag": 1, "data": -9223372036854775808, "want": bytes([0x08, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x01])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_int64(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_float32(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0.0, "want": bytes([0x0d, 0x00, 0x00, 0x00, 0x00])},
            {"name": "positive small", "tag": 1, "data": 3.14, "want": bytes([0x0d, 0xc3, 0xf5, 0x48, 0x40])},
            {"name": "negative small", "tag": 1, "data": -3.14, "want": bytes([0x0d, 0xc3, 0xf5, 0x48, 0xc0])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_float32(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_float64(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0.0, "want": bytes([0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])},
            {"name": "positive small", "tag": 1, "data": 3.14159265359, "want": bytes([0x09, 0xea, 0x2e, 0x44, 0x54, 0xfb, 0x21, 0x09, 0x40])},
            {"name": "negative small", "tag": 1, "data": -3.14159265359, "want": bytes([0x09, 0xea, 0x2e, 0x44, 0x54, 0xfb, 0x21, 0x09, 0xc0])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_float64(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_bool(self):
        test_cases = [
            {"name": "true", "tag": 1, "data": True, "want": bytes([0x08, 0x01])},
            {"name": "false", "tag": 1, "data": False, "want": bytes([0x08, 0x00])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_bool(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_fixed32(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x0d, 0x00, 0x00, 0x00, 0x00])},
            {"name": "small value", "tag": 1, "data": 127, "want": bytes([0x0d, 0x7f, 0x00, 0x00, 0x00])},
            {"name": "max uint32", "tag": 1, "data": 4294967295, "want": bytes([0x0d, 0xff, 0xff, 0xff, 0xff])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_fixed32(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_fixed64(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])},
            {"name": "small value", "tag": 1, "data": 127, "want": bytes([0x09, 0x7f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])},
            {"name": "max uint64", "tag": 1, "data": 18446744073709551615, "want": bytes([0x09, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_fixed64(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_uint32(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x08, 0x00])},
            {"name": "small value", "tag": 1, "data": 127, "want": bytes([0x08, 0x7f])},
            {"name": "max uint32", "tag": 1, "data": 4294967295, "want": bytes([0x08, 0xff, 0xff, 0xff, 0xff, 0x0f])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_uint32(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

    def test_writer_append_uint64(self):
        test_cases = [
            {"name": "zero", "tag": 1, "data": 0, "want": bytes([0x08, 0x00])},
            {"name": "small value", "tag": 1, "data": 127, "want": bytes([0x08, 0x7f])},
            {"name": "max uint64", "tag": 1, "data": 18446744073709551615, "want": bytes([0x08, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x01])},
        ]
        buf = bytearray(64)
        for tc in test_cases:
            with self.subTest(name=tc["name"]):
                writer = Writer(buf)
                writer.append_uint64(tc["tag"], tc["data"])
                self.assertEqual(tc["want"], bytes(buf[0:writer.pos]))

if __name__ == '__main__':
    unittest.main()