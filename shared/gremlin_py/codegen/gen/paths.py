"""
Provides functionality for handling file paths in the Protocol Buffer to Python code generator.
This module handles path transformations between source proto files and their corresponding
generated Python output files.
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

class PathError(Exception):
    """Custom exception for path-related errors."""
    pass

def output_path(rel_path: str, out_folder: str) -> str:
    """
    Generates the output path for a Python file based on the input proto file path.
    Maintains the directory structure relative to the output folder while
    changing the extension to .py.

    Given an input path like "path/to/file.proto" and output folder "out",
    generates a path like "out/path/to/file.py"

    Parameters:
      - rel_path: Relative path of the input proto file
      - out_folder: Base output directory for generated files

    Returns:
      String containing the complete output path.
    
    Raises:
      PathError: If the input path structure is invalid.
    """
    if not rel_path:
        raise PathError("Invalid path: input path cannot be empty.")

    directory, filename = os.path.split(rel_path)
    
    # Generate output filename with .py extension
    base_filename, _ = os.path.splitext(filename)
    output_filename = f"{base_filename}.py"

    directory = directory.replace('-', '_')
    output_filename = output_filename.replace('-', '_')

    # Combine components into final path
    return os.path.join(out_folder, directory, output_filename)