import unittest
from .buffer import ParserBuffer
from .syntax import Syntax
from .errors import ParsingError, ProtoError

class TestSyntaxParser(unittest.TestCase):

    def test_invalid_syntax_keyword(self):
        buf = ParserBuffer("synz;")
        self.assertIsNone(Syntax.parse(buf))
        self.assertEqual(0, buf.offset)

    def test_different_keyword(self):
        buf = ParserBuffer("package test;")
        self.assertIsNone(Syntax.parse(buf))
        self.assertEqual(0, buf.offset)

    def test_valid_proto3_single_quotes(self):
        buf = ParserBuffer("syntax = 'proto3';")
        syntax = Syntax.parse(buf)
        self.assertEqual(Syntax(start=0, end=18), syntax)
        self.assertEqual(18, buf.offset)

    def test_valid_proto3_double_quotes(self):
        buf = ParserBuffer("syntax = \"proto3\";")
        syntax = Syntax.parse(buf)
        self.assertEqual(Syntax(start=0, end=18), syntax)
        self.assertEqual(18, buf.offset)

    def test_missing_assignment(self):
        buf = ParserBuffer("syntax proto3;")
        with self.assertRaises(ProtoError) as cm:
            Syntax.parse(buf)
        self.assertEqual(ParsingError.AssignmentExpected, cm.exception.error_code)

    def test_missing_semicolon(self):
        buf = ParserBuffer("syntax = 'proto3'")
        with self.assertRaises(ProtoError) as cm:
            Syntax.parse(buf)
        self.assertEqual(ParsingError.SemicolonExpected, cm.exception.error_code)

    def test_invalid_version(self):
        buf = ParserBuffer("syntax = 'proto4';")
        with self.assertRaises(ProtoError) as cm:
            Syntax.parse(buf)
        self.assertEqual(ParsingError.InvalidSyntaxVersion, cm.exception.error_code)

if __name__ == '__main__':
    unittest.main()