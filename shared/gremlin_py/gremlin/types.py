# //! Core protocol buffer wire format types and error definitions
# //! Provides type definitions for protocol buffer wire format encoding/decoding
#
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

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, Generic

# Field number in protocol buffer message
ProtoWireNumber = int


# Wire types defined by protocol buffer specification
class ProtoWireType(Enum):
    VARINT = 0
    FIXED64 = 1
    BYTES = 2
    START_GROUP = 3
    END_GROUP = 4
    FIXED32 = 5


# Complete tag information for a protocol buffer field
@dataclass
class ProtoTag:
    number: ProtoWireNumber
    wire: ProtoWireType
    size: int


# Generic sized value wrapper
T = TypeVar('T')


@dataclass
class Sized(Generic[T]):
    size: int
    value: T


# Basic numeric types with size information
SizedU32 = Sized[int]
SizedU64 = Sized[int]
SizedI32 = Sized[int]
SizedI64 = Sized[int]
SizedF32 = Sized[float]
SizedF64 = Sized[float]

# Other sized basic types
SizedBool = Sized[bool]
SizedBytes = Sized[bytes]
SizedMemoryView = Sized[memoryview]


# Protocol buffer encoding/decoding errors
class GremlinError(Exception):
    """Base exception for Gremlin errors."""
    pass


class InvalidVarIntError(GremlinError):
    """Invalid variable integer encoding."""
    pass


class InvalidTagError(GremlinError):
    """Invalid field tag."""
    pass


class InvalidDataError(GremlinError):
    """Data doesn't match expected format."""
    pass