from enum import IntEnum

# Wire types defined by protocol buffer specification
class ProtoWireType(IntEnum):
    VARINT = 0
    FIXED64 = 1
    BYTES = 2
    START_GROUP = 3
    END_GROUP = 4
    FIXED32 = 5

def size_field_tag(field_number: int, wire_type: ProtoWireType) -> int:
    tag = (field_number << 3) | wire_type.value
    return ((tag | 1).bit_length() + 6) // 7

def generate_tag_bytes(field_number: int, wire_type: ProtoWireType) -> bytes:
    """
    Generates the bytes for a Protobuf varint.
    Optimized with fast paths for 1-5 byte values (covering up to ~34 billion).
    """

    value = (field_number << 3) | wire_type.value

    if value < 0:
        # Negative numbers are always 10 bytes in standard Protobuf (int32/int64)
        # Treated as 64-bit unsigned integers (2's complement)
        value += (1 << 64)
    
    # --- PATH 1: 1 Byte (< 128) ---
    if value < 0x80:
        return bytes([value])

    # --- PATH 2: 2 Bytes (< 16,384) ---
    if value < 0x4000:
        return bytes([
            (value & 0x7F) | 0x80,
            value >> 7
        ])

    # --- PATH 3: 3 Bytes (< 2,097,152) ---
    if value < 0x200000:
        return bytes([
            (value & 0x7F) | 0x80,
            (value >> 7) & 0x7F | 0x80,
            value >> 14
        ])

    # --- PATH 4: 4 Bytes (< 268,435,456) ---
    if value < 0x10000000:
        return bytes([
            (value & 0x7F) | 0x80,
            (value >> 7) & 0x7F | 0x80,
            (value >> 14) & 0x7F | 0x80,
            value >> 21
        ])

    # --- PATH 5: 5 Bytes (< 34,359,738,368) ---
    if value < 0x800000000:
        return bytes([
            (value & 0x7F) | 0x80,
            (value >> 7) & 0x7F | 0x80,
            (value >> 14) & 0x7F | 0x80,
            (value >> 21) & 0x7F | 0x80,
            value >> 28
        ])

    # --- FALLBACK: 6-10 Bytes ---
    # We collect integers into a list first, then convert to bytes once.
    # This is faster than bytearray concatenation or appending.
    chunks = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            chunks.append(byte | 0x80)
        else:
            chunks.append(byte)
            break
            
    return bytes(chunks)