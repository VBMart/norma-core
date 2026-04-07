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

"""
Provides functionality for generating Python enum types from Protocol Buffer definitions.
This module handles the conversion of protobuf enum definitions into their Python counterparts,
ensuring proper naming conventions and value handling.
"""

import io
from typing import Set, List

from .. import parser
from .fields import naming


class PythonEnumEntry:
    """Represents a single entry in a Python enum definition."""
    def __init__(self, const_name: str, value: int):
        self.const_name = const_name
        self.value = value


class PythonEnum:
    """
    Represents a complete Python enum type definition.
    Manages the generation of enum types from Protocol Buffer definitions,
    including handling of entries, naming, and code generation.
    """

    def __init__(self, src: parser.Enum, scope_name: str, names: Set[str]):
        self.src = src
        
        entries_list: List[PythonEnumEntry] = []
        
        # Process enum fields
        has_zero_value = self._process_enum_fields(src, entries_list)

        # Ensure zero value exists
        if not has_zero_value:
            self._add_default_unknown_field(entries_list)
            
        self.entries = entries_list

        # Generate enum type name and full path
        prefixed_name = f"{scope_name}$${src.name.name}" if scope_name else src.name.name
        self.const_name = naming.struct_name(prefixed_name, names)
        self.full_name = self.const_name

    def create_enum_def(self) -> str:
        """Generates the Python code representation of this enum."""
        buf = io.StringIO()
        
        buf.write(f"class {self.const_name}(enum.IntEnum):\n")

        if not self.entries:
            buf.write("    pass\n")
        else:
            # Write entries with consistent formatting
            for entry in self.entries:
                buf.write(f"    {entry.const_name} = {entry.value}\n")
        
        return buf.getvalue()

    def _process_enum_fields(self, src: parser.Enum, entries_list: List[PythonEnumEntry]) -> bool:
        entries_names: Set[str] = set()
        has_zero_value = False

        for field in src.fields:
            if field.index == 0:
                has_zero_value = True
            
            field_name = naming.enum_field_name(field.name, entries_names)
            entries_list.append(PythonEnumEntry(field_name, field.index))
        
        return has_zero_value

    def _add_default_unknown_field(self, entries_list: List[PythonEnumEntry]):
        entries_names: Set[str] = set()
        # Collect existing names to avoid collision
        for entry in entries_list:
            entries_names.add(entry.const_name)

        field_name = naming.enum_field_name("___protobuf_unknown", entries_names)
        entries_list.insert(0, PythonEnumEntry(field_name, 0))