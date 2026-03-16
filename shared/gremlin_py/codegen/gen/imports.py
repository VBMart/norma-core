"""
Provides functionality for collecting and managing import dependencies in Protocol Buffer files.
This module analyzes message definitions to identify all required imports across nested messages,
fields, oneofs, and maps.
"""

#               .'\   /`.
#             .'.-.`-'-.`.
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

from typing import List

from .. import parser


class ImportCollector:
    """
    ImportCollector analyzes Protocol Buffer definitions to gather all required imports.
    It tracks unique dependencies and ensures no duplicate imports are included.
    """

    def __init__(self):
        self.targets: List[parser.ProtoFile] = []

    @staticmethod
    def collect_from_file(file: parser.ProtoFile) -> List[parser.ProtoFile]:
        """
        Creates a new ImportCollector and analyzes the given file for imports.
        Processes all messages and their nested components to find dependencies.
        """
        collector = ImportCollector()

        # Process all top-level messages
        for msg in file.messages:
            collector._collect_from_message(msg)

        return collector.targets

    def _add_import(self, import_target: parser.ProtoFile) -> None:
        """
        Adds a new import target if it's not already present.
        Maintains uniqueness of imports to prevent duplicates.
        """
        if import_target not in self.targets:
            self.targets.append(import_target)

    def _collect_from_message(self, msg: parser.Message) -> None:
        """
        Recursively collects imports from a message and all its components.
        Processes nested messages, fields, oneofs, and maps to find all dependencies.
        """
        # Process nested messages recursively
        self._collect_nested_message_imports(msg)

        # Process different types of fields
        self._collect_field_imports(msg)
        self._collect_oneof_imports(msg)
        self._collect_map_imports(msg)

    def _collect_nested_message_imports(self, msg: parser.Message) -> None:
        """Processes nested messages within a message."""
        for sub_msg in msg.messages:
            self._collect_from_message(sub_msg)

    def _collect_field_imports(self, msg: parser.Message) -> None:
        """Processes regular fields within a message."""
        for field in msg.fields:
            if field.f_type.ref_import:
                self._add_import(field.f_type.ref_import)

    def _collect_oneof_imports(self, msg: parser.Message) -> None:
        """Processes oneof fields within a message."""
        for oneof in msg.oneofs:
            for field in oneof.fields:
                if field.f_type.ref_import:
                    self._add_import(field.f_type.ref_import)

    def _collect_map_imports(self, msg: parser.Message) -> None:
        """Processes map fields within a message."""
        for map_field in msg.maps:
            if map_field.value_type.ref_import:
                self._add_import(map_field.value_type.ref_import)