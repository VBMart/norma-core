import unittest
from .buffer import ParserBuffer
from .errors import ParsingError, ProtoError
from .lexems import (
    str_lit,
    ident,
    full_ident,
    int_lit,
    float_lit,
    field_type,
    message_type,
    parse_range,
    parse_ranges,
    constant
)

class TestLexems(unittest.TestCase):

    def test_str_literals(self):
        buf = ParserBuffer(' "hello" ')
        self.assertEqual(str_lit(buf), "hello")

        buf = ParserBuffer(" 'hello' ")
        self.assertEqual(str_lit(buf), "hello")

        buf = ParserBuffer(' "hello\\"" ')
        self.assertEqual(str_lit(buf), 'hello\\"')

        buf = ParserBuffer("'\\xDEAD'")
        self.assertEqual(str_lit(buf), "\\xDEAD")

    def test_ident(self):
        buf = ParserBuffer("hello ")
        self.assertEqual(ident(buf), "hello")

        buf = ParserBuffer("hello123 ")
        self.assertEqual(ident(buf), "hello123")

        buf = ParserBuffer("hello_123 ")
        self.assertEqual(ident(buf), "hello_123")

        buf = ParserBuffer("hello_123_ ")
        self.assertEqual(ident(buf), "hello_123_")

        with self.assertRaises(ProtoError) as cm:
            buf = ParserBuffer("1hello_123_ ")
            ident(buf)
        self.assertEqual(cm.exception.error_code, ParsingError.IdentifierShouldStartWithLetter)

    def test_full_ident(self):
        buf = ParserBuffer("hello ")
        self.assertEqual(full_ident(buf), "hello")

        buf = ParserBuffer("hello123.world ")
        self.assertEqual(full_ident(buf), "hello123.world")

        buf = ParserBuffer("hello_123.world ")
        self.assertEqual(full_ident(buf), "hello_123.world")

        buf = ParserBuffer("hello_123_.world ")
        self.assertEqual(full_ident(buf), "hello_123_.world")

        with self.assertRaises(ProtoError) as cm:
            buf = ParserBuffer("hello123.456 ")
            full_ident(buf)
        self.assertEqual(cm.exception.error_code, ParsingError.IdentifierShouldStartWithLetter)

    def test_int_lit(self):
        buf = ParserBuffer("123 ")
        self.assertEqual(int_lit(buf), "123")

        buf = ParserBuffer("0x123 ")
        self.assertEqual(int_lit(buf), "0x123")

        buf = ParserBuffer("0X123 ")
        self.assertEqual(int_lit(buf), "0X123")

        buf = ParserBuffer("01239 ")
        self.assertEqual(int_lit(buf), "0123")

        buf = ParserBuffer("0 ")
        self.assertEqual(int_lit(buf), "0")

        buf = ParserBuffer("-123 ")
        self.assertEqual(int_lit(buf), "-123")

    def test_float_lit(self):
        buf = ParserBuffer("inf ")
        self.assertEqual(float_lit(buf), "inf")

        buf = ParserBuffer("nan ")
        self.assertEqual(float_lit(buf), "nan")

        buf = ParserBuffer(".456 ")
        self.assertEqual(float_lit(buf), ".456")

        buf = ParserBuffer(".1e10 ")
        self.assertEqual(float_lit(buf), ".1e10")

        buf = ParserBuffer(".0 ")
        self.assertEqual(float_lit(buf), ".0")

        buf = ParserBuffer("123.456 ")
        self.assertEqual(float_lit(buf), "123.456")

    def test_field_type(self):
        buf = ParserBuffer("float name")
        self.assertEqual(field_type(buf), "float")
        
        buf = ParserBuffer("sint64 val")
        self.assertEqual(field_type(buf), "sint64")

    def test_message_type(self):
        buf = ParserBuffer(".complex.message.Type name")
        self.assertEqual(message_type(buf), ".complex.message.Type")

    def test_parse_range(self):
        buf = ParserBuffer("1 to 2")
        self.assertEqual(parse_range(buf), "1 to 2")

        buf = ParserBuffer("9 to max")
        self.assertEqual(parse_range(buf), "9 to max")

        buf = ParserBuffer("9,12")
        self.assertEqual(parse_range(buf), "9")

    def test_parse_ranges(self):
        buf = ParserBuffer("2, 15, 9 to 11")
        res = parse_ranges(buf)
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], "2")
        self.assertEqual(res[1], "15")
        self.assertEqual(res[2], "9 to 11")

    def test_parse_x_str(self):
        buf = ParserBuffer('"\\xfe"')
        c = str_lit(buf)
        self.assertEqual(c, "\\xfe")

    def test_parse_hex_const(self):
        buf = ParserBuffer("0xFFFFFFFF")
        c = constant(buf)
        self.assertEqual(c, "0xFFFFFFFF")

    def test_trigraph_const(self):
        buf = ParserBuffer('"? \\? ?? \\?? \\??? ??/ ?\\?-"')
        c = constant(buf)
        self.assertEqual(c, '"? \\? ?? \\?? \\??? ??/ ?\\?-"')

if __name__ == '__main__':
    unittest.main()