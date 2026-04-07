import unittest
import os
import tempfile
import shutil
from .paths import find_proto_files, find_root

class PathsTest(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory with dummy proto files for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.sub_dir = os.path.join(self.test_dir, "a", "b")
        os.makedirs(self.sub_dir)

        self.proto_files_paths = [
            os.path.realpath(os.path.join(self.test_dir, "test1.proto")),
            os.path.realpath(os.path.join(self.sub_dir, "test2.proto")),
            os.path.realpath(os.path.join(self.sub_dir, "test3.proto")),
        ]

        for path in self.proto_files_paths:
            with open(path, "w") as f:
                f.write("syntax = 'proto3';")

        # Create a non-proto file to ensure it's ignored
        with open(os.path.join(self.sub_dir, "not_a_proto.txt"), "w") as f:
            f.write("hello")

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_find_proto_files(self):
        """Test the find_proto_files function."""
        found_files = find_proto_files(self.test_dir)

        # Use sets for comparison to ignore order
        self.assertEqual(set(found_files), set(self.proto_files_paths))

        # Test with a subdirectory
        found_in_sub = find_proto_files(self.sub_dir)
        self.assertEqual(len(found_in_sub), 2)
        self.assertIn(os.path.realpath(os.path.join(self.sub_dir, "test2.proto")), found_in_sub)
        self.assertIn(os.path.realpath(os.path.join(self.sub_dir, "test3.proto")), found_in_sub)

    def test_find_root(self):
        """Test the find_root function."""
        paths = [
            "/a/b/c/d/file1.proto",
            "/a/b/d/c/file2.proto",
        ]
        root = find_root(paths)
        self.assertEqual(root, "/a/b")

    def test_find_root_no_branching(self):
        """Test find_root where paths don't branch."""
        paths = [
            "/a/b/c/file1.proto",
        ]
        with self.assertRaisesRegex(ValueError, "No common root found"):
            find_root(paths)

    def test_find_root_at_top_level(self):
        """Test find_root where the branch is at the top level."""
        paths = [
            "/a/file1.proto",
            "/b/file2.proto",
        ]
        root = find_root(paths)
        self.assertEqual(root, "/")

    def test_find_root_empty_list(self):
        """Test find_root with an empty list of paths."""
        with self.assertRaisesRegex(ValueError, "Cannot find root of an empty list"):
            find_root([])


if __name__ == '__main__':
    unittest.main()