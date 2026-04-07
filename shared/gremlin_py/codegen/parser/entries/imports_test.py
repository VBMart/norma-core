import unittest
from .buffer import ParserBuffer
from .imports import Import, ImportType

class TestImport(unittest.TestCase):

    def test_parse_weak_import(self):
        buf = ParserBuffer('import weak "foo/bar";')
        imp = Import.parse(buf)
        self.assertIsNotNone(imp)
        self.assertEqual(0, imp.start)
        self.assertEqual(22, imp.end)
        self.assertEqual(ImportType.WEAK, imp.i_type)
        self.assertEqual("foo/bar", imp.path)
        self.assertTrue(imp.is_weak())
        self.assertFalse(imp.is_public())

    def test_parse_public_import(self):
        buf = ParserBuffer('import public "foo/bar";')
        imp = Import.parse(buf)
        self.assertIsNotNone(imp)
        self.assertEqual(0, imp.start)
        self.assertEqual(24, imp.end)
        self.assertEqual(ImportType.PUBLIC, imp.i_type)
        self.assertEqual("foo/bar", imp.path)
        self.assertFalse(imp.is_weak())
        self.assertTrue(imp.is_public())

    def test_parse_regular_import(self):
        buf = ParserBuffer('import "foo/bar-baz.proto";')
        imp = Import.parse(buf)
        self.assertIsNotNone(imp)
        self.assertEqual(0, imp.start)
        self.assertEqual(27, imp.end)
        self.assertIsNone(imp.i_type)
        self.assertEqual("foo/bar-baz.proto", imp.path)
        self.assertFalse(imp.is_weak())
        self.assertFalse(imp.is_public())

    def test_parse_path_components(self):
        buf = ParserBuffer('import "foo/bar/baz.proto";')
        imp = Import.parse(buf)
        self.assertIsNotNone(imp)
        self.assertEqual("baz.proto", imp.basename())
        self.assertEqual("foo/bar", imp.directory())

    def test_parse_multiple_imports(self):
        import_text = (
            'import "google/protobuf/any.proto";'
            'import "google/protobuf/duration.proto";'
            'import "google/protobuf/field_mask.proto";'
            'import "google/protobuf/struct.proto";'
            'import "google/protobuf/timestamp.proto";'
            'import "google/protobuf/wrappers.proto";'
        )
        buf = ParserBuffer(import_text)

        for _ in range(6):
            imp = Import.parse(buf)
            self.assertIsNotNone(imp)
            self.assertTrue(imp.path.startswith("google/protobuf/"))
            self.assertTrue(imp.path.endswith(".proto"))

        self.assertIsNone(Import.parse(buf))

if __name__ == '__main__':
    unittest.main()