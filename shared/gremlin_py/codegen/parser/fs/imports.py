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

from __future__ import annotations
from typing import List, Dict
import os

from ..entries.file import ProtoFile
from ..entries.imports import Import, ImportType

class ResolveError(Exception):
    pass

class TargetFileNotFoundError(ResolveError):
    pass

class ImportResolver:
    """
    ImportResolver handles resolving imports between protobuf files.
    """

    def __init__(self, base_path: str, files: List[ProtoFile]):
        self.base_path = base_path
        self.files = files
        self.files_map: Dict[str, ProtoFile] = {}

        # Build lookup map of files by path
        for file in self.files:
            if file.path:
                self.files_map[file.path] = file

    def resolve_target_files(self):
        """
        Iterates through all files and resolves their imports.
        """
        for file in self.files:
            self._resolve_file_imports(file)

    def _resolve_file_imports(self, file: ProtoFile):
        """
        Resolves all imports for a single file.
        """
        if not file.path:
            return

        for imp in file.imports:
            self._resolve_import(file.path, imp)

    def _resolve_import(self, file_path: str, imp: Import):
        """
        Resolves a single import by finding its target file.
        """
        # Build full target path
        target_path = os.path.join(self.base_path, imp.path)

        # Look up target file
        target = self.files_map.get(target_path)
        if target:
            imp.target = target
        else:
            print(f"cannot resolve import {imp.path} from {file_path} with root {self.base_path}")
            raise TargetFileNotFoundError()

    def resolve_public_imports(self):
        """
        Propagates public imports through all files.
        """
        for file in self.files:
            self._resolve_file_public_imports(file)

    def _resolve_file_public_imports(self, file: ProtoFile):
        """
        Propagates public imports for a single file.
        """
        
        for imp in file.imports:
            if not imp.target:
                continue
            self._propagate_public_imports(file, imp.target)

    def _propagate_public_imports(self, file: ProtoFile, target: ProtoFile):
        """
        Propagates public imports from a target file to the importing file.
        """
        from ..entries.imports import Import

        for target_import in target.imports:
            if target_import.i_type == ImportType.PUBLIC:
                file.imports.append(Import(
                    start=0,
                    end=0,
                    path=target_import.path,
                    i_type=ImportType.PUBLIC,
                    target=target_import.target
                ))

def resolve_imports(base: str, files: List[ProtoFile]):
    """
    Resolves imports between protobuf files.
    """
    resolver = ImportResolver(base, files)
    resolver.resolve_target_files()
    resolver.resolve_public_imports()