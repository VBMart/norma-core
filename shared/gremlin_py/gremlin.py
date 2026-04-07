#!/usr/bin/env python3

"""
Command-line tool for generating Python code from Protocol Buffer definitions.
"""

import argparse
import os
import sys

# Add the project root to the Python path to allow importing the codegen module.
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

from codegen import generate_protobuf

def main():
    """
    Parses command-line arguments and runs the Protocol Buffer code generator.
    """
    parser = argparse.ArgumentParser(description="Generate Python code from .proto files.")
    parser.add_argument(
        "--proto-root",
        required=True,
        help="The root directory containing the .proto source files."
    )
    parser.add_argument(
        "--target-root",
        required=True,
        help="The root directory where the generated Python files will be written."
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="The root of the project, used for resolving cross-file imports."
    )
    parser.add_argument(
        "--gremlin-import-path",
        default="gremlin",
        help="The Python import path for the gremlin library. Defaults to 'gremlin'."
    )

    args = parser.parse_args()

    # Create target directory and __init__.py if they don't exist.
    if not os.path.exists(args.target_root):
        os.makedirs(args.target_root)

    init_py_path = os.path.join(args.target_root, "__init__.py")
    if not os.path.exists(init_py_path):
        with open(init_py_path, "w") as f:
            pass

    generate_protobuf(
        proto_root=args.proto_root,
        target_root=args.target_root,
        project_root=args.project_root,
        gremlin_import_path=args.gremlin_import_path,
    )

if __name__ == "__main__":
    main()