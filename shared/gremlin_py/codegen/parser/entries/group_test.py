import unittest
from .buffer import ParserBuffer
from .group import Group

class GroupTest(unittest.TestCase):
    def test_basic_group(self):
        buf = ParserBuffer(
            """
            group Result = 1 {
              required string url = 2;
              optional string title = 3;
            }
            """
        )
        group = Group.parse(buf)
        self.assertIsNotNone(group)
        self.assertGreater(group.end, group.start)

    def test_group_with_modifiers(self):
        # Test optional group
        buf_optional = ParserBuffer("optional group OptionalGroup = 1 { required int32 id = 2; }")
        group_optional = Group.parse(buf_optional)
        self.assertIsNotNone(group_optional)
        self.assertGreater(group_optional.end, group_optional.start)

        # Test required group
        buf_required = ParserBuffer("required group RequiredGroup = 3 { optional string name = 4; }")
        group_required = Group.parse(buf_required)
        self.assertIsNotNone(group_required)
        self.assertGreater(group_required.end, group_required.start)

        # Test repeated group
        buf_repeated = ParserBuffer("repeated group RepeatedGroup = 5 { required bool flag = 6; }")
        group_repeated = Group.parse(buf_repeated)
        self.assertIsNotNone(group_repeated)
        self.assertGreater(group_repeated.end, group_repeated.start)

    def test_nested_groups(self):
        buf = ParserBuffer(
            """
            group Outer = 1 {
              required string name = 2;
              optional group Inner = 3 {
                required int32 value = 4;
              }
            }
            """
        )
        group = Group.parse(buf)
        self.assertIsNotNone(group)
        self.assertGreater(group.end, group.start)

    def test_not_a_group(self):
        buf = ParserBuffer("message NotAGroup { required string name = 1; }")
        result = Group.parse(buf)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()