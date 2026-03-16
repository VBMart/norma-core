"""
Provides buffered file output functionality for generating Python source code files.
This module handles proper formatting of generated code including indentation,
comments, and multi-line strings while maintaining efficient I/O operations.
"""

#               .'\   /`.
#             .'.-.`-'.-.`.
#        ..._:   .-. .-.   :_...
#      .'    '-.(o ) (o ).-'    `.
#     :  _    _ _`~(_)~`_ _    _  :
#    :  /:   ' .-=_   _=-. `   ;\  :
#    :   :|-.._  '     `  _..-|:   :
#     :   `:| |`:-:-.-:-:'| |:'   :
#      `.   `.| | | | | | |.'   .'
#        `.   `-:_| | |_:-'   .'
#          `-._   ````    _.-'
#              ``-------''
#
# Created by ab, 25.11.2025

import os
from typing import TextIO
from contextlib import contextmanager

class FileOutput:
    """
    FileOutput provides a writer for generating formatted Python source files.
    Handles proper indentation, comments, and multi-line string output.
    """

    INDENT_SIZE: int = 4
    COMMENT_PREFIX: str = "# "

    _depth: int
    _file: TextIO

    def __init__(self, path: str):
        """
        Initialize a new FileOutput with the given path.
        Creates the necessary directory structure and opens the file for writing.

        :param path: Output file path
        """
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        self._file = open(path, "w", encoding="utf-8")
        self._depth = 0

    def close(self) -> None:
        """
        Closes the file.
        Should be called when finished writing to ensure all data is written.
        """
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def depth(self) -> int:
        return self._depth

    @depth.setter
    def depth(self, value: int):
        self._depth = value

    @contextmanager
    def indent(self):
        """A context manager for indentation."""
        self._depth += 1
        try:
            yield
        finally:
            self._depth -= 1

    def write_prefix(self) -> None:
        """
        Writes the current indentation prefix based on depth.
        Each indentation level adds INDENT_SIZE spaces.
        """
        if self._depth > 0:
            spaces = self._depth * self.INDENT_SIZE
            self._file.write(" " * spaces)

    def write_comment(self, comment: str) -> None:
        """
        Writes a single-line comment with proper indentation.
        Automatically adds the comment prefix and a newline.

        :param comment: Comment text to write
        """
        self.write_prefix()
        self._file.write(self.COMMENT_PREFIX)
        self._file.write(comment)
        self._file.write("\n")

    def linebreak(self) -> None:
        """
        Writes a single linebreak without any indentation.
        """
        self._file.write("\n")

    def write_string(self, value: str) -> None:
        """
        Writes a multi-line string with proper indentation for each line.
        Maintains consistent indentation across line breaks.

        :param value: String content to write
        """
        prefix = " " * (self._depth * self.INDENT_SIZE)
        lines = value.split("\n")
        for line in lines:
            self._file.write(prefix)
            self._file.write(line)
            self._file.write("\n")

    def continue_string(self, value: str) -> None:
        """
        Continues writing a string without adding indentation or linebreaks.
        Useful for building complex strings across multiple write operations.

        :param value: String content to write
        """
        self._file.write(value)