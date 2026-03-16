import unittest
from .buffer import ParserBuffer
from .option import Option

class OptionTest(unittest.TestCase):
    def test_basic_option(self):
        # Test standalone option parsing
        buf = ParserBuffer('option java_package = "com.example.foo";')
        opt = Option.parse(buf)
        self.assertIsNotNone(opt)
        self.assertEqual("java_package", opt.name)
        self.assertEqual('"com.example.foo"', opt.value)
        self.assertEqual(0, opt.start)
        self.assertEqual(40, opt.end)

    def test_option_list(self):
        # Test multiple options in a list
        buf = ParserBuffer('[java_package = "com.example.foo", another = true]')
        opts = Option.parse_list(buf)
        self.assertIsNotNone(opts)
        self.assertEqual(2, len(opts))

        self.assertEqual("java_package", opts[0].name)
        self.assertEqual('"com.example.foo"', opts[0].value)

        self.assertEqual("another", opts[1].name)
        self.assertEqual("true", opts[1].value)

    def test_float_options(self):
        # Test floating point option values
        buf = ParserBuffer("[default = 51.5]")
        opts = Option.parse_list(buf)
        self.assertIsNotNone(opts)
        self.assertEqual(1, len(opts))
        self.assertEqual("default", opts[0].name)
        self.assertEqual("51.5", opts[0].value)

    def test_empty_string_options(self):
        # Test empty string option values
        buf = ParserBuffer('[default = ""]')
        opts = Option.parse_list(buf)
        self.assertIsNotNone(opts)
        self.assertEqual(1, len(opts))
        self.assertEqual("default", opts[0].name)
        self.assertEqual('""', opts[0].value)

if __name__ == '__main__':
    unittest.main()