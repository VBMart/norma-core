from __future__ import annotations
import os

from typing import List, Optional, Set

from .. import parser
from . import paths
from .fields import naming
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .file import PythonFile


class PythonImport:
    """
    Represents a Python import statement, handling both system imports and imports from other proto files.
    """
    alias: str
    path: str
    src: Optional[parser.ProtoFile]
    target: Optional[PythonFile]
    is_system: bool
    from_import: bool

    def __init__(self, src: Optional[parser.ProtoFile], alias: str, path: str, from_import: bool = False):
        self.src = src
        self.alias = alias
        self.path = path
        self.is_system = src is None
        self.target = None
        self.from_import = from_import

    def resolve(self, files: List[PythonFile]) -> None:
        """
        Resolves this import against a list of generated Python files.
        Links the import to its corresponding target file for cross-file references.
        """
        if self.is_system:
            return

        if self.src is None:
            raise Exception("Cannot resolve import without a source proto file")

        for f in files:
            if f.file and self.src.path == f.file.path:
                self.target = f
                return

        raise Exception(f"Failed to resolve import for proto file: {self.src.path}")

    def code(self) -> str:
        """
        Generates the Python code representation of this import.
        """
        if self.from_import:
            return f"from {self.path} import {self.alias}"
        return f"import {self.path} as {self.alias}"


def resolve_import(
    src: parser.ProtoFile,
    proto_root: str,
    target_root: str,
    project_root: str,
    import_path: str,
    names: Set[str],
) -> PythonImport:
    """
    Resolves an import path to create a PythonImport instance.
    Handles path resolution between proto files and generated Python files,
    ensuring proper module paths are created.
    """
    # Get the path relative to proto_root
    rel_to_proto = os.path.relpath(import_path, proto_root)

    # Generate output path in target directory
    out_path = paths.output_path(rel_to_proto, target_root)

    # Get path relative to project root
    rel_to_project = os.path.relpath(out_path, project_root)

    # Generate module path from the path relative to project root
    module_path = os.path.splitext(rel_to_project)[0].replace(os.path.sep, '.')

    # Generate import alias from filename
    file_name = os.path.splitext(os.path.basename(import_path))[0]
    alias = naming.import_alias(file_name, names)
    names.add(alias)

    return PythonImport(src, alias, module_path)