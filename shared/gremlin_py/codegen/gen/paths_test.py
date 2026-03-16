import unittest
import os
from .paths import output_path, PathError

class PathsTest(unittest.TestCase):

    def test_output_path(self):
        """Tests standard path transformation."""
        rel_path = os.path.join("path", "to", "file.proto")
        out_folder = "out"
        
        out_path = output_path(rel_path, out_folder)
        expected = os.path.join("out", "path", "to", "file.py")
        
        self.assertEqual(expected, out_path)

    def test_output_path_no_dir(self):
        """Tests path transformation for a file in the root."""
        rel_path = "file.proto"
        out_folder = "out"
        
        out_path = output_path(rel_path, out_folder)
        expected = os.path.join("out", "file.py")
        
        self.assertEqual(expected, out_path)

    def test_output_path_empty_rel_path(self):
        """Tests handling of an empty input path."""
        with self.assertRaises(PathError):
            output_path("", "out")

    def test_output_path_different_extension(self):
        """Tests that the extension is correctly replaced."""
        rel_path = os.path.join("path", "to", "another.file.txt")
        out_folder = "gen"
        
        out_path = output_path(rel_path, out_folder)
        expected = os.path.join("gen", "path", "to", "another.file.py")
        
        self.assertEqual(expected, out_path)

if __name__ == '__main__':
    unittest.main()