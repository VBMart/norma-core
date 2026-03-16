"""
This module handles the conversion of Protocol Buffer identifiers to valid Python identifiers.
It ensures proper naming conventions, handles keywords, and maintains uniqueness of names
across different contexts (constants, fields, methods, etc.).
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

import keyword
from typing import Set

# List of Python keywords that need special handling to avoid naming conflicts
KEYWORDS = set(keyword.kwlist)

def is_keyword(name: str) -> bool:
    """Check if a given name is a Python keyword."""
    return name in KEYWORDS

def make_const_name(name: str) -> str:
    """Convert a name to SCREAMING_SNAKE_CASE for constants."""
    if not name:
        return ""

    result = []
    
    # Handle first character - prefix with '_' if it starts with a digit
    if name[0].isdigit():
        result.append('_')
    result.append(name[0].upper())

    # Process remaining characters
    for i, c in enumerate(name[1:], start=1):
        prev_char_in_source = name[i-1]

        # Add underscore before uppercase letters when needed
        if c.isupper() and result and result[-1] != '_' and not prev_char_in_source.isupper():
            result.append('_')

        # Preserve single underscores
        if c == '_' and result and result[-1] != '_':
            result.append('_')
            continue

        # Convert alphanumeric chars to uppercase
        if c.isalnum():
            result.append(c.upper())

    # Remove trailing underscore if present
    if result and result[-1] == '_':
        result.pop()

    return "".join(result)

def make_snake_case(name: str) -> str:
    """Convert a name to snake_case for struct fields."""
    if not name:
        return ""

    result = []

    # First character must be a-zA-Z_
    c = name[0]
    if c.isdigit():
        result.append('_')
    if c.isalpha() or c.isdigit() or c == '_':
        result.append(c.lower())
    else:
        result.append('_')

    # Add underscore before capital letters (camelCase -> snake_case)
    for c in name[1:]:
        if c.isupper() and result and result[-1] != '_':
            result.append('_')

        # Convert to lowercase and handle special characters
        if c.isalnum():
            result.append(c.lower())
        else:
            result.append('_')

        # Collapse multiple underscores
        if len(result) >= 2 and result[-1] == '_' and result[-2] == '_':
            result.pop()

    res_str = "".join(result)
    
    # Append underscore to keyword names
    if is_keyword(res_str):
        return res_str + '_'
    
    return res_str

def make_camel_case(name: str, start_upper: bool) -> str:
    """Convert a name to camelCase for methods or PascalCase for types."""
    if not name:
        return ""

    # If the special separator is present, process each part and join with an underscore.
    if '$$' in name:
        parts = name.split('$$')
        # The first part respects start_upper, subsequent parts are always PascalCase.
        processed_parts = [make_camel_case(part, start_upper if i == 0 else True) for i, part in enumerate(parts)]
        return "_".join(processed_parts)

    # The original logic for a single segment.
    result = []
    capitalize_next = False

    # Handle first character
    c = name[0]
    if c.isdigit():
        result.append('_')
    
    if c.isalpha() or c.isdigit() or c == '_':
        if start_upper:
            result.append(c.upper())
        else:
            result.append(c.lower())
    else:
        result.append('_')

    # Handle special characters and capitalization
    for c in name[1:]:
        if c == '_' or not c.isalnum():
            if c == '$':
                result.append('_')
            capitalize_next = True
            continue

        if capitalize_next:
            result.append(c.upper())
            capitalize_next = False
        else:
            result.append(c)

    res_str = "".join(result)
    
    # Append underscore to keyword names
    if is_keyword(res_str):
        return res_str + '_'
    
    return res_str

def get_unused_name(base_name: str, used_names: Set[str]) -> str:
    """Generate a unique name by appending numbers if needed."""
    if base_name not in used_names:
        used_names.add(base_name)
        return base_name

    counter = 1
    while True:
        new_name = f"{base_name}{counter}"
        if new_name not in used_names:
            used_names.add(new_name)
            return new_name
        counter += 1

# Public interface functions

def const_name(proto_name: str, used_names: Set[str]) -> str:
    """Convert a Protocol Buffer name to a Python constant name (SCREAMING_SNAKE_CASE)."""
    name = make_const_name(proto_name)
    return get_unused_name(name, used_names)

def struct_name(proto_name: str, used_names: Set[str]) -> str:
    """Convert a Protocol Buffer name to a Python class name (PascalCase)."""
    name = make_camel_case(proto_name, start_upper=True)
    return get_unused_name(name, used_names)

def enum_field_name(proto_name: str, used_names: Set[str]) -> str:
    """Convert a Protocol Buffer name to a Python enum field name (SCREAMING_SNAKE_CASE)."""
    name = make_const_name(proto_name)
    return get_unused_name(name, used_names)

def struct_field_name(proto_name: str, used_names: Set[str]) -> str:
    """Convert a Protocol Buffer name to a Python struct field name (snake_case)."""
    name = make_snake_case(proto_name)
    return get_unused_name(name, used_names)

def struct_method_name(proto_name: str, used_names: Set[str]) -> str:
    """Convert a Protocol Buffer name to a Python method name (snake_case)."""
    name = make_snake_case(proto_name)
    return get_unused_name(name, used_names)

def import_alias(proto_name: str, used_names: Set[str]) -> str:
    """Convert a Protocol Buffer name to a Python import alias (snake_case)."""
    name = make_snake_case(proto_name)
    return get_unused_name(name, used_names)