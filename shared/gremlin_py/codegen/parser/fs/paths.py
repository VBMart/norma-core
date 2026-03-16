import os
from typing import List

def find_proto_files(base_path: str) -> List[str]:
    """
    Finds all .proto files recursively starting from the given base path.

    Args:
        base_path: The path to the directory to start searching from.

    Returns:
        A list of absolute, real paths to all found .proto files.
    """
    proto_files = []
    for root_dir, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".proto"):
                proto_files.append(os.path.realpath(os.path.join(root_dir, file)))
    return proto_files


class _FsNode:
    """Represents a node in the filesystem tree. Used internally by find_root."""

    def __init__(self, path: str):
        self.path = path
        self.children: List['_FsNode'] = []
        self.files = 0

    def find_or_create_child(self, part: str) -> '_FsNode':
        """Finds or creates a child node with the given path part."""
        full_path = os.path.join(self.path, part)
        for child in self.children:
            if child.path == full_path:
                return child
        new_node = _FsNode(full_path)
        self.children.append(new_node)
        return new_node


def find_root(paths: List[str]) -> str:
    """
    Finds the common root directory of all given paths.

    This function identifies the deepest common directory that serves as a
    branching point for the given file paths. It is a direct port of a Zig
    implementation and has a specific behavior: it raises an error if no
    clear branching point is found (e.g., if all paths are in a single
    directory or form a linear chain).

    Args:
        paths: A list of file paths.

    Returns:
        The path to the deepest common directory.

    Raises:
        ValueError: If no common root can be found or the input list is empty.
    """
    if not paths:
        raise ValueError("Cannot find root of an empty list of paths")

    # This implementation assumes POSIX-like paths, as in the original code and tests.
    root = _FsNode(os.path.sep)

    for path in paths:
        current = root
        directory = os.path.dirname(path)
        if not directory:
            raise ValueError(f"Cannot get directory from path: {path}")

        # Split path and build/traverse the tree
        parts = directory.split(os.path.sep)
        for part in parts:
            if not part:
                continue
            current = current.find_or_create_child(part)
        current.files += 1

    # Find the deepest directory that is a common ancestor
    target = root
    while len(target.children) == 1 and target.files == 0:
        target = target.children[0]

    if len(target.children) == 0:
        raise ValueError("No common root found (no branching subdirectories)")

    return target.path