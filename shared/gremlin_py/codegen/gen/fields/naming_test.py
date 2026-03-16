import unittest
from . import naming

class TestNaming(unittest.TestCase):

    def test_naming_conventions(self):
        used_names = set()

        # Test const_name
        name_const = naming.const_name("testName", used_names)
        self.assertEqual("TEST_NAME", name_const)

        # Test const_name with a name that is already used
        name_const1 = naming.const_name("TEST_NAME", used_names)
        self.assertEqual("TEST_NAME1", name_const1)

        # Test enum_field_name
        name_ef = naming.enum_field_name("testName", used_names)
        self.assertEqual("TEST_NAME2", name_ef)

        # Test struct_field_name
        name_sf = naming.struct_field_name("testName", used_names)
        self.assertEqual("test_name", name_sf)

        # Test struct_method_name
        name_sm = naming.struct_method_name("test_name", used_names)
        self.assertEqual("test_name1", name_sm)

        # Test keyword handling for struct_field_name
        name_keyword = naming.struct_field_name("for", used_names)
        self.assertEqual("for_", name_keyword)

        # Test keyword handling for struct_method_name
        name_keyword2 = naming.struct_method_name("while", used_names)
        self.assertEqual("while_", name_keyword2)

if __name__ == '__main__':
    unittest.main()