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
# Created by ab, 14.11.2024

"""
Main module for the Protocol Buffer to Python code generator.
This module orchestrates the generation process, handling file parsing,
code generation, and file output management.
"""

import os
from typing import List

from . import parser
from .gen.file import PythonFile
from .gen.output import FileOutput
from .gen.paths import output_path


class GeneratorError(Exception):
    """Base exception for generator errors."""
    pass


class PathResolutionError(GeneratorError):
    """File path could not be resolved."""
    pass


class FileWriteError(GeneratorError):
    """File could not be created or written."""
    pass


class ParserError(GeneratorError):
    """Parser encountered an error."""
    pass


class ReferenceResolutionError(GeneratorError):
    """Reference resolution failed."""
    pass


def _create_file(
    proto_file: parser.ProtoFile,
    proto_root: str,
    target_root: str,
    project_root: str,
    gremlin_import_path: str,
) -> PythonFile:
    """
    Creates a PythonFile instance from a Protocol Buffer file.
    Handles path resolution and initialization of the Python source file.
    """
    try:
        # Get path relative to proto root
        rel_to_proto = os.path.relpath(proto_file.path, proto_root)

        # Generate output path
        out_path = output_path(rel_to_proto, target_root)

        # Initialize Python file
        return PythonFile(
            out_path,
            proto_file,
            proto_root,
            target_root,
            project_root,
            gremlin_import_path,
        )
    except (ValueError, IOError) as e:
        raise FileWriteError(f"Failed to create file for {proto_file.path}: {e}") from e


def generate_protobuf(
    proto_root: str,
    target_root: str,
    project_root: str,
    gremlin_import_path: str = "gremlin",
) -> None:
    """
    Main function to generate Python code from Protocol Buffer definitions.
    Orchestrates the complete generation process including parsing, reference resolution,
    and code generation.
    """
    try:
        # Parse all proto files
        print(f"Parsing from: {proto_root}")
        parsed_files = parser.parse(proto_root)
        print(f"Parsed {len(parsed_files.files)} files.")
    except Exception as e:
        raise ParserError(f"Failed to parse proto files: {e}") from e

    # Create PythonFile instances
    files: List[PythonFile] = []
    for proto_file in parsed_files.files:
        files.append(_create_file(
            proto_file,
            proto_root,
            target_root,
            project_root,
            gremlin_import_path,
        ))

    # Resolve cross-file references
    try:
        _resolve_references(files)
    except Exception as e:
        raise ReferenceResolutionError(f"Failed to resolve references: {e}") from e

    # Generate code for each file
    _generate_code(files)


def _resolve_references(files: List[PythonFile]) -> None:
    """
    Resolves cross-file references between all generated files.
    """
    # Resolve imports between files
    for py_file in files:
        py_file.resolve_imports(files)

    # Resolve internal references
    for py_file in files:
        py_file.resolve_refs()


def _generate_code(files: List[PythonFile]) -> None:
    """
    Generates code for all files and writes to disk.
    """
    for py_file in files:
        try:
            with FileOutput(py_file.out_path) as out_file:
                py_file.write(out_file)
        except IOError as e:
            raise FileWriteError(f"Failed to write file {py_file.out_path}: {e}") from e