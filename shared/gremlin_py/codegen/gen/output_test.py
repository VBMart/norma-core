import unittest
import os
import tempfile
import shutil

from .output import FileOutput


class FileOutputTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Tests that the file and its parent directories are created."""
        file_path = os.path.join(self.test_dir, "path", "to", "file.py")
        with FileOutput(file_path):
            self.assertTrue(os.path.exists(file_path))

    def test_write_prefix(self):
        """Tests that the correct indentation is written."""
        file_path = os.path.join(self.test_dir, "test.py")
        with FileOutput(file_path) as f:
            f.depth = 1
            f.write_prefix()
            f.continue_string("hello")

        with open(file_path, "r") as f:
            content = f.read()
            self.assertEqual("    hello", content)

    def test_write_comment(self):
        """Tests that a comment is written with the correct indentation and prefix."""
        file_path = os.path.join(self.test_dir, "test.py")
        with FileOutput(file_path) as f:
            f.depth = 1
            f.write_comment("This is a comment")

        with open(file_path, "r") as f:
            content = f.read()
            self.assertEqual("    # This is a comment\n", content)

    def test_linebreak(self):
        """Tests that a newline character is written."""
        file_path = os.path.join(self.test_dir, "test.py")
        with FileOutput(file_path) as f:
            f.continue_string("hello")
            f.linebreak()
            f.continue_string("world")

        with open(file_path, "r") as f:
            content = f.read()
            self.assertEqual("hello\nworld", content)

    def test_write_string(self):
        """Tests that a multi-line string is written with the correct indentation."""
        file_path = os.path.join(self.test_dir, "test.py")
        with FileOutput(file_path) as f:
            f.depth = 1
            f.write_string("line1\nline2")

        with open(file_path, "r") as f:
            content = f.read()
            self.assertEqual("    line1\n    line2\n", content)

    def test_continue_string(self):
        """Tests that a string is written without any indentation or newlines."""
        file_path = os.path.join(self.test_dir, "test.py")
        with FileOutput(file_path) as f:
            f.continue_string("hello")
            f.continue_string(" world")

        with open(file_path, "r") as f:
            content = f.read()
            self.assertEqual("hello world", content)

    def test_context_manager(self):
        """Tests that the file is closed when exiting the context manager."""
        file_path = os.path.join(self.test_dir, "test.py")
        f = FileOutput(file_path)
        with f:
            f.continue_string("hello")
        self.assertTrue(f._file.closed)


if __name__ == '__main__':
    unittest.main()