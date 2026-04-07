import unittest
from .buffer import ParserBuffer

class TestParserBuffer(unittest.TestCase):

    def test_whitespaces(self):
        buf = ParserBuffer("  \t\n\rtest")
        buf.skip_spaces()
        self.assertEqual(5, buf.offset)

        buf1 = ParserBuffer("  \t\n\rtest", offset=3)
        buf1.skip_spaces()
        self.assertEqual(5, buf1.offset)

        buf2 = ParserBuffer(" test")
        buf2.skip_spaces()
        self.assertEqual(1, buf2.offset)

    def test_prefix(self):
        buf = ParserBuffer("import 'abc';")
        self.assertTrue(buf.check_str_and_shift("import"))

        buf = ParserBuffer("import 'abc';")
        self.assertTrue(buf.check_str_with_space_and_shift("import"))

    def test_large_comment(self):
        buf = ParserBuffer(
            "// Protocol Buffers - Google's data interchange format\n"
            "// Copyright 2008 Google Inc.  All rights reserved.\n"
            "//\n"
            "// Use of this source code is governed by a BSD-style\n"
            "// license that can be found in the LICENSE file or at\n"
            "// https://developers.google.com/open-source/licenses/bsd\n"
            "//\n"
            "// Test schema for proto3 messages.  This test schema is used by:\n"
            "//\n"
            "// - benchmarks\n"
            "// - fuzz tests\n"
            "// - conformance tests\n"
            "\n"
            "syntax = \"proto3\";"
        )
        buf.skip_spaces()
        self.assertTrue(buf.check_str_and_shift("syntax"))

    def test_large_multiline_comment(self):
        buf = ParserBuffer(
            "/* Protocol Buffers - Google's data interchange format\n"
            "   another line\n"
            "   * and this one\n"
            " */\n"
            "syntax = \"proto3\""
        )
        buf.skip_spaces()
        self.assertTrue(buf.check_str_and_shift("syntax"))

if __name__ == '__main__':
    unittest.main()