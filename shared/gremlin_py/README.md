# gremlin.py

A zero-dependency Google Protocol Buffers implementation in pure Python (no protoc required)

## Installation & Setup

To use the code generator, you can run the `gremlin.py` script directly:

```bash
python3 shared/gremlin_py/gremlin.py \
    --proto-root path/to/your/proto/files \
    --target-root path/to/your/output/directory \
    --project-root path/to/your/project
```

## Features

*   Zero dependencies
*   Pure Python implementation (no `protoc` required)
*   Compatible with Protocol Buffers version 2 and 3
*   Simple integration with your project
*   Single allocation for serialization (including complex recursive messages)
*   Lazy parsing - parses only required complex fields

## Generated code

Given a protobuf definition:

```proto
syntax = "proto3";

message User {
  string name = 1;
  uint64 id   = 2;
  repeated string tags = 10;
}
```

Gremlin will generate an equivalent Python `dataclass`:

```python
from dataclasses import dataclass
from typing import Optional, List
import gremlin

@dataclass
class User:
    name: Optional[str] = None
    id: int = 0
    tags: Optional[List[str]] = None

    def calc_protobuf_size(self) -> int:
        ...

    def encode(self) -> bytes:
        ...

    def encode_to(self, writer: gremlin.Writer) -> None:
        ...

# Reader for lazy parsing
class UserReader:

    def __init__(self, src: memoryview):
        ...

    def get_name(self) -> str:
        ...

    def get_id(self) -> int:
        ...

    def get_tags(self) -> List[str]:
        ...
```

## Running Tests

To run the tests for `gremlin.py`, you can execute the following command from the root of the repository:

```bash
python -m unittest discover -p "*_test.py"
```

This will discover and run all the tests in the `tests` directory.