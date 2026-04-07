# Size calculation functions for protocol buffer wire format types
# Used to determine byte size of encoded values before writing

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

"""Size calculation functions for protocol buffer wire format types."""

from . import types

def size_varint(value: int) -> int:
    return ((value | 1).bit_length() + 6) // 7

def size_signed_varint(value: int) -> int:
    return size_varint(value << 1 if value >= 0 else (value << 1) ^ -1)

# Variable-length integer types
def size_i32(value: int) -> int:
    return size_varint(value if value >= 0 else value + (1 << 64))

def size_i64(value: int) -> int:
    return size_varint(value if value >= 0 else value + (1 << 64))

# Zigzag encoded signed integer types
def size_si32(value: int) -> int:
    """Calculate size of a zigzag encoded 32-bit signed integer."""
    return size_signed_varint(value)

def size_si64(value: int) -> int:
    """Calculate size of a zigzag encoded 64-bit signed integer."""
    return size_signed_varint(value)