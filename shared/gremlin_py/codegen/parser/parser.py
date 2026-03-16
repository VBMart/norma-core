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
import sys
from dataclasses import dataclass, field
from typing import List

from .entries.buffer import ParserBuffer
from .entries.file import ProtoFile
from .entries.errors import ProtoError
from .fs import paths
from .fs.imports import resolve_imports
from .resolver import resolve_references

@dataclass
class ParseResult:
    """
    Represents the result of parsing protocol buffer files.
    Owns all the parsed data and associated buffers.
    """
    files: List[ProtoFile] = field(default_factory=list)
    bufs: List[ParserBuffer] = field(default_factory=list)
    root: str = ""

def print_error(path: str, err: ProtoError, buf: ParserBuffer):
    """
    Formats and prints a parser error with context about where the error occurred.
    """
    err_line = buf.calc_line_number()
    line_start = buf.calc_line_start()
    line_end = buf.calc_line_end()
    
    # Ensure err_pos is not negative
    err_pos = max(0, buf.offset - line_start)
    
    # Safely slice the buffer
    err_fragment = buf.buf[err_pos : buf.offset + line_end]

    print(f"Failed to parse file {path} [offset = {buf.offset}]:", file=sys.stderr)
    print(f"Error: {err}", file=sys.stderr)
    print(f"{err_line}: {err_fragment}", file=sys.stderr)

    if line_start > 0:
        spaces = ' ' * (line_start - 1)
        print(f"\n{spaces}^\n", file=sys.stderr)
    else:
        print("\n", file=sys.stderr)

def parse(base_path: str) -> ParseResult:
    """
    Parse protocol buffer files starting from the given base path.
    Returns a ParseResult containing all parsed files and their buffers.
    """
    proto_files = paths.find_proto_files(base_path)
    
    if not os.path.isabs(base_path):
        root = os.path.realpath(base_path)
    else:
        root = base_path

    parsed_files: List[ProtoFile] = []
    parser_buffers: List[ParserBuffer] = []

    for file_path in proto_files:
        try:
            buffer = ParserBuffer.from_file(file_path)
            proto_file = ProtoFile.parse(buffer)
            proto_file.path = file_path
            parsed_files.append(proto_file)
            parser_buffers.append(buffer)
        except ProtoError as err:
            print_error(file_path, err, buffer)
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}", file=sys.stderr)

    resolve_imports(root, parsed_files)
    resolve_references(parsed_files)

    return ParseResult(
        files=parsed_files,
        bufs=parser_buffers,
        root=base_path,
    )