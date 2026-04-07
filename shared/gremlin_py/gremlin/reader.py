# //! Protocol buffer wire format reader
# //! Provides functionality for decoding protocol buffer encoded messages
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

import struct
from typing import Union

from .types import (
    ProtoWireType,
    ProtoTag,
    InvalidTagError,
    InvalidVarIntError,
    InvalidDataError,
    SizedU32,
    SizedU64,
    SizedI32,
    SizedI64,
    SizedF32,
    SizedF64,
    SizedBool,
    SizedBytes,
    SizedMemoryView,
)

# Maximum value for a 32-bit integer
MAX_I32 = 2**31 - 1


class Reader:
    """Reader for decoding protocol buffer wire format"""

    def __init__(self, data: Union[bytes, bytearray, memoryview]):
        """Initialize a new reader with given data buffer"""
        self.buf = memoryview(data)

    def bytes(self) -> memoryview:
        """Get underlying buffer"""
        return self.buf

    def read_tag_at(self, offset: int) -> ProtoTag:
        """Read tag information at given offset"""
        tag_data = self._read_varint_at(offset)
        if tag_data.value >> 3 > MAX_I32:
            raise InvalidTagError("Invalid tag value")

        return ProtoTag(
            number=tag_data.value >> 3,
            wire=ProtoWireType(tag_data.value & 0x07),
            size=tag_data.size,
        )

    def skip_data(self, offset: int, wire: ProtoWireType) -> int:
        """Skip data of given wire type at offset"""
        if wire == ProtoWireType.VARINT:
            size = self._get_varint_size(offset)
            return offset + size
        elif wire == ProtoWireType.FIXED32:
            return offset + 4
        elif wire == ProtoWireType.FIXED64:
            return offset + 8
        elif wire == ProtoWireType.BYTES:
            size_data = self._read_varint_at(offset)
            return offset + size_data.size + size_data.value
        elif wire == ProtoWireType.START_GROUP:
            current_offset = offset
            while True:
                tag = self.read_tag_at(current_offset)
                current_offset += tag.size
                if tag.wire == ProtoWireType.END_GROUP:
                    return current_offset
                current_offset = self.skip_data(current_offset, tag.wire)
        else:
            raise InvalidTagError("Invalid wire type")

    def _get_varint_size(self, offset: int) -> int:
        """Get size of varint at offset"""
        for i in range(10):
            if not self._has_next(offset, i):
                raise InvalidVarIntError("Incomplete varint data")
            if self.buf[offset + i] < 0x80:
                return i + 1
        return 10

    def _read_fixed32_at(self, offset: int) -> int:
        """Read 32-bit fixed integer at offset"""
        if not self._has_next(offset, 3):
            raise InvalidDataError("Incomplete fixed32 data")
        return struct.unpack_from('<I', self.buf, offset)[0]

    def _read_fixed64_at(self, offset: int) -> int:
        """Read 64-bit fixed integer at offset"""
        if not self._has_next(offset, 7):
            raise InvalidDataError("Incomplete fixed64 data")
        return struct.unpack_from('<Q', self.buf, offset)[0]

    def read_bytes(self, offset: int) -> SizedBytes:
        """Read length-delimited bytes at offset"""
        size_data = self._read_varint_at(offset)
        start = offset + size_data.size
        end = start + size_data.value
        return SizedBytes(
            value=self.buf[start:end].tobytes(),
            size=size_data.size + size_data.value,
        )

    def read_bytes_view(self, offset: int) -> SizedMemoryView:
        """Read length-delimited bytes at offset without allocation"""
        size_data = self._read_varint_at(offset)
        start = offset + size_data.size
        end = start + size_data.value
        return SizedMemoryView(
            value=self.buf[start:end],
            size=size_data.size + size_data.value,
        )

    def read_varint(self, offset: int) -> SizedU64:
        """Read raw varint at offset"""
        return self._read_varint_at(offset)

    def read_uint64(self, offset: int) -> SizedU64:
        """Read unsigned 64-bit integer at offset"""
        return self.read_varint(offset)

    def read_uint32(self, offset: int) -> SizedU32:
        """Read unsigned 32-bit integer at offset"""
        result = self._read_varint_at(offset)
        return SizedU32(value=result.value & 0xFFFFFFFF, size=result.size)

    def read_int64(self, offset: int) -> SizedI64:
        """Read signed 64-bit integer at offset"""
        result = self._read_varint_at(offset)
        return SizedI64(
            value=struct.unpack("<q", struct.pack("<Q", result.value))[0],
            size=result.size,
        )

    def read_int32(self, offset: int) -> SizedI32:
        """Read signed 32-bit integer at offset"""
        result = self._read_varint_at(offset)
        value = result.value & 0xFFFFFFFF
        return SizedI32(
            value=struct.unpack("<i", struct.pack("<I", value))[0], size=result.size
        )

    def read_sint64(self, offset: int) -> SizedI64:
        """Read zigzag encoded signed 64-bit integer at offset"""
        return self._read_signed_varint_at(offset)

    def read_sint32(self, offset: int) -> SizedI32:
        """Read zigzag encoded signed 32-bit integer at offset"""
        result = self._read_signed_varint_at(offset)
        return SizedI32(value=result.value, size=result.size)

    def read_bool(self, offset: int) -> SizedBool:
        """Read boolean value at offset"""
        result = self._read_varint_at(offset)
        return SizedBool(value=result.value != 0, size=result.size)

    def read_float32(self, offset: int) -> SizedF32:
        """Read 32-bit float at offset"""
        value = self._read_fixed32_at(offset)
        return SizedF32(value=struct.unpack('<f', struct.pack('<I', value))[0], size=4)

    def read_float64(self, offset: int) -> SizedF64:
        """Read 64-bit float at offset"""
        value = self._read_fixed64_at(offset)
        return SizedF64(value=struct.unpack('<d', struct.pack('<Q', value))[0], size=8)

    def read_fixed32(self, offset: int) -> SizedU32:
        """Read fixed 32-bit unsigned integer at offset"""
        return SizedU32(value=self._read_fixed32_at(offset), size=4)

    def read_fixed64(self, offset: int) -> SizedU64:
        """Read fixed 64-bit unsigned integer at offset"""
        return SizedU64(value=self._read_fixed64_at(offset), size=8)

    def read_sfixed32(self, offset: int) -> SizedI32:
        """Read fixed 32-bit signed integer at offset"""
        value = self._read_fixed32_at(offset)
        return SizedI32(value=struct.unpack('<i', struct.pack('<I', value))[0], size=4)

    def read_sfixed64(self, offset: int) -> SizedI64:
        """Read fixed 64-bit signed integer at offset"""
        value = self._read_fixed64_at(offset)
        return SizedI64(value=struct.unpack('<q', struct.pack('<Q', value))[0], size=8)

    def has_next(self, offset: int) -> bool:
        """Check if there is more data to read from offset"""
        return offset < len(self.buf)

    def _has_next(self, offset: int, size: int) -> bool:
        """Check if offset + size is within buffer bounds"""
        return (offset + size) < len(self.buf)

    def _read_signed_varint_at(self, offset: int) -> SizedI64:
        """Read zigzag encoded signed varint at offset"""
        result = self._read_varint_at(offset)
        # ZigZag decoding
        value = (result.value >> 1) ^ (-(result.value & 1))
        return SizedI64(value=value, size=result.size)

    def _read_varint_at(self, offset: int) -> SizedU64:
        """Read raw varint at offset"""
        value = 0
        shift = 0
        i = 0
        while i < 10:
            if not self._has_next(offset, i):
                raise InvalidVarIntError("Incomplete varint data")

            b = self.buf[offset + i]
            if shift >= 64:
                raise InvalidVarIntError("Varint too long")

            value |= (b & 0x7F) << shift

            if b < 0x80:
                return SizedU64(value=value, size=i + 1)

            if shift > 57:  # 64 - 7
                raise InvalidVarIntError("Varint too long")
            shift += 7
            i += 1

        raise InvalidVarIntError("Varint too long")
