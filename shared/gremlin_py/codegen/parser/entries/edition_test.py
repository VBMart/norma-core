import unittest
from .buffer import ParserBuffer
from .edition import Edition
from .errors import ParsingError, ProtoError


class TestEditionParser(unittest.TestCase):

    def test_valid_edition(self):
        buf = ParserBuffer("edition = \"2018\";")
        edition = Edition.parse(buf)
        self.assertIsNotNone(edition)
        assert edition is not None
        self.assertEqual("2018", edition.edition)
        self.assertEqual(0, edition.start)
        self.assertEqual(17, edition.end)

    def test_missing_assignment(self):
        buf = ParserBuffer("edition \"2018\";")
        with self.assertRaises(ProtoError) as cm:
            Edition.parse(buf)
        self.assertEqual(ParsingError.AssignmentExpected, cm.exception.error_code)

    def test_missing_semicolon(self):
        buf = ParserBuffer("edition = \"2018\"")
        with self.assertRaises(ProtoError) as cm:
            Edition.parse(buf)
        self.assertEqual(ParsingError.SemicolonExpected, cm.exception.error_code)

    def test_invalid_string_literal(self):
        buf = ParserBuffer("edition = 2018;")
        with self.assertRaises(ProtoError) as cm:
            Edition.parse(buf)
        self.assertEqual(ParsingError.InvalidStringLiteral, cm.exception.error_code)

    def test_invalid_edition_keyword(self):
        buf = ParserBuffer("ed;")
        self.assertIsNone(Edition.parse(buf))
        self.assertEqual(0, buf.offset)

    def test_different_keyword(self):
        buf = ParserBuffer("package test;")
        self.assertIsNone(Edition.parse(buf))
        self.assertEqual(0, buf.offset)

if __name__ == '__main__':
    unittest.main()