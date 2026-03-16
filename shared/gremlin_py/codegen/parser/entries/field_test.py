import unittest

from .buffer import ParserBuffer
from .field import NormalField, MessageMapField, MessageOneOfField
from .scoped_name import ScopedName


class FieldTest(unittest.TestCase):
    def test_normal_field(self):
        scope = ScopedName("")
        buf = ParserBuffer("string name = 1;")
        f = NormalField.parse(scope, buf)
        self.assertEqual("string", f.f_type.src)
        self.assertEqual("name", f.f_name)
        self.assertEqual(1, f.index)

    def test_map_field(self):
        scope = ScopedName("")
        buf = ParserBuffer("map<string, Project> projects = 3;")
        f = MessageMapField.parse(scope, buf)
        self.assertIsNotNone(f)
        self.assertEqual("string", f.key_type)
        self.assertEqual("Project", f.value_type.src)
        self.assertEqual("projects", f.f_name)

    def test_oneof_field(self):
        scope = ScopedName("")
        buf = ParserBuffer("""
            oneof foo {
                string name = 4;
                SubMessage sub_message = 9;
            }
        """)
        f = MessageOneOfField.parse(scope, buf)
        self.assertIsNotNone(f)
        self.assertEqual("foo", f.name)
        self.assertEqual(2, len(f.fields))


if __name__ == '__main__':
    unittest.main()