# ParserBuffer provides utilities for parsing text content with common operations
# like handling whitespace, comments, and basic syntax elements. It's particularly
# useful for implementing parsers for domain-specific languages or file formats.

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
# Created by ab, 24.11.2025

from .errors import ParsingError, ProtoError

WHITESPACE_CHARS = [' ', '\t', '\n', '\r']

class ParserBuffer:
    """
    A buffer for parsing text content with utilities for handling common
    parsing operations like whitespace, comments, and basic syntax elements.
    """

    def __init__(self, buf: str, offset: int = 0):
        """
        Initializes a new ParserBuffer with the given text content.

        :param buf: The text content to be parsed.
        :param offset: The initial parsing position within the buffer.
        """
        self.buf = buf
        self.offset = offset

    @classmethod
    def from_file(cls, path: str):
        """
        Initializes a ParserBuffer by reading the entire contents of a file.

        :param path: The path to the file to be read.
        :return: A new ParserBuffer instance.
        """
        with open(path, 'r') as f:
            return cls(f.read())

    def check_str_and_shift(self, prefix: str) -> bool:
        """
        Checks if the buffer starts with the given prefix at the current offset.
        If it matches, advances the offset past the prefix.

        :param prefix: The prefix to check for.
        :return: True if the prefix matches, False otherwise.
        """
        if self.buf.startswith(prefix, self.offset):
            self.offset += len(prefix)
            return True
        return False

    def check_str_with_space_and_shift(self, prefix: str) -> bool:
        """
        Checks if the buffer starts with the given prefix followed by whitespace.
        If it matches, advances the offset past both the prefix and the whitespace.

        :param prefix: The prefix to check for.
        :return: True if the prefix matches, False otherwise.
        """
        if not self.buf.startswith(prefix, self.offset):
            return False

        if (self.offset + len(prefix) < len(self.buf) and
                self.buf[self.offset + len(prefix)] in WHITESPACE_CHARS):
            self.offset += len(prefix) + 1
            return True
        return False

    def skip_spaces(self):
        """
        Skips over any whitespace and comments at the current position.
        Handles both single-line (//) and multi-line (/* */) comments.
        """
        while self.offset < len(self.buf) and self.buf[self.offset] in WHITESPACE_CHARS:
            self.offset += 1

        c = self.char()
        if c != '/':
            return

        if self.offset + 1 >= len(self.buf):
            raise ProtoError(ParsingError.UnexpectedEOF)

        if self.buf[self.offset + 1] == '/':
            while self.offset < len(self.buf) and self.char() != '\n':
                self.offset += 1
            self.skip_spaces()
        elif self.buf[self.offset + 1] == '*':
            self.offset += 2
            while True:
                if self.offset >= len(self.buf):
                    raise ProtoError(ParsingError.UnexpectedEOF)
                if self.buf[self.offset:self.offset+2] == '*/':
                    self.offset += 2
                    self.skip_spaces()
                    break
                self.offset += 1

    def check_and_shift(self, expected: str) -> bool:
        """
        Checks if the current character matches the expected one and advances if it does.

        :param expected: The character to check for.
        :return: True if the character matches, False otherwise.
        """
        if self.offset >= len(self.buf):
            raise ProtoError(ParsingError.UnexpectedEOF)

        if self.buf[self.offset] == expected:
            self.offset += 1
            return True
        return False

    def char(self) -> str | None:
        """
        Gets the current character without advancing the offset.

        :return: The current character, or None if at the end of the buffer.
        """
        if self.offset >= len(self.buf):
            return None
        return self.buf[self.offset]

    def should_shift_next(self) -> str:
        """
        Gets the current character and advances the offset.

        :return: The current character.
        :raises ParsingError.UnexpectedEOF: If at the end of the buffer.
        """
        if self.offset >= len(self.buf):
            raise ProtoError(ParsingError.UnexpectedEOF)

        c = self.buf[self.offset]
        self.offset += 1
        return c

    def semicolon(self):
        """
        Expects and consumes a semicolon, skipping any whitespace before it.
        """
        self.skip_spaces()
        if self.offset >= len(self.buf) or self.should_shift_next() != ';':
            raise ProtoError(ParsingError.SemicolonExpected)

    def assignment(self):
        """
        Expects and consumes an equals sign, skipping any whitespace before and after.
        """
        self.skip_spaces()
        if self.should_shift_next() != '=':
            raise ProtoError(ParsingError.AssignmentExpected)
        self.skip_spaces()

    def open_bracket(self):
        """
        Expects and consumes an opening brace, skipping any whitespace before and after.
        """
        self.skip_spaces()
        if self.should_shift_next() != '{':
            raise ProtoError(ParsingError.BracketExpected)
        self.skip_spaces()

    def close_bracket(self):
        """
        Expects and consumes a closing brace, skipping any whitespace before and after.
        """
        self.skip_spaces()
        if self.should_shift_next() != '}':
            raise ProtoError(ParsingError.BracketExpected)
        self.skip_spaces()

    def calc_line_number(self) -> int:
        """
        Calculates the current line number (1-based).

        :return: The current line number.
        """
        return self.buf.count('\n', 0, self.offset) + 1

    def calc_line_start(self) -> int:
        """
        Calculates the column position from the start of the current line.

        :return: The column position.
        """
        last_newline = self.buf.rfind('\n', 0, self.offset)
        if last_newline == -1:
            return self.offset
        return self.offset - last_newline - 1

    def calc_line_end(self) -> int:
        """
        Calculates the number of characters remaining until the end of the current line.

        :return: The number of characters remaining.
        """
        next_newline = self.buf.find('\n', self.offset)
        if next_newline == -1:
            return len(self.buf) - self.offset
        return next_newline - self.offset