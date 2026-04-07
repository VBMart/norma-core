# //! Protocol buffer wire format writer
# //! Handles encoding of protocol buffer messages according to wire format specification
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
from .types import ProtoWireNumber, ProtoWireType
from typing import Union

class Writer:
    """Writes protocol buffer encoded data to a buffer"""

    def __init__(self, buf: bytearray):
        """Initialize writer with output buffer"""
        self.buf = buf
        self.pos = 0

    def reset(self):
        """Reset writer position"""
        self.pos = 0

    def append_bytes(self, tag: bytes, data: Union[bytes, bytearray, memoryview]):
        """Write length-delimited bytes with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)

        self.append_varint(len(data))
        self.append_raw_bytes(data)

    def append_bytes_size_with_tag(self, tag: bytes, size: int):
        """Write length-delimited bytes with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_varint(size)

    def append_bytes_tag(self, tag: ProtoWireNumber, length: int):
        """Write bytes length prefix only"""
        self.append_tag(tag, ProtoWireType.BYTES)
        self.append_varint(length)

    def append_bool(self, tag: bytes, data: bool):
        """Write boolean value with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_bool_without_tag(data)

    def append_bool_without_tag(self, data: bool):
        """Write boolean value without tag"""
        self.append_varint(1 if data else 0)

    def append_int32(self, tag: bytes, data: int):
        """Write signed 32-bit integer with tag bytes"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_varint(data & 0xFFFFFFFFFFFFFFFF)

    def append_int32_without_tag(self, data: int):
        """Write signed 32-bit integer without tag"""
        self.append_varint(data & 0xFFFFFFFFFFFFFFFF)

    def append_int64(self, tag: bytes, data: int):
        """Write signed 64-bit integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_int64_without_tag(data)

    def append_int64_without_tag(self, data: int):
        """Write signed 64-bit integer without tag"""
        self.append_varint(data & 0xFFFFFFFFFFFFFFFF)

    def append_uint32(self, tag: bytes, data: int):
        """Write unsigned 32-bit integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_uint32_without_tag(data)

    def append_uint32_without_tag(self, data: int):
        """Write unsigned 32-bit integer without tag"""
        self.append_varint(data)

    def append_uint64(self, tag: bytes, data: int):
        """Write unsigned 64-bit integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_uint64_without_tag(data)

    def append_uint64_without_tag(self, data: int):
        """Write unsigned 64-bit integer without tag"""
        self.append_varint(data)

    def append_sint32(self, tag: bytes, data: int):
        """Write zigzag encoded 32-bit integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_sint32_without_tag(data)

    def append_sint32_without_tag(self, data: int):
        """Write zigzag encoded 32-bit integer without tag"""
        self._append_signed_varint(data)

    def append_sint64(self, tag: bytes, data: int):
        """Write zigzag encoded 64-bit integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_sint64_without_tag(data)

    def append_sint64_without_tag(self, data: int):
        """Write zigzag encoded 64-bit integer without tag"""
        self._append_signed_varint(data)

    def append_fixed32(self, tag: bytes, data: int):
        """Write fixed-width 32-bit unsigned integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_fixed32_without_tag(data)

    def append_fixed32_without_tag(self, data: int):
        """Write fixed-width 32-bit unsigned integer without tag"""
        self._internal_append_fixed32(data)

    def append_fixed64(self, tag: bytes, data: int):
        """Write fixed-width 64-bit unsigned integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_fixed64_without_tag(data)

    def append_fixed64_without_tag(self, data: int):
        """Write fixed-width 64-bit unsigned integer without tag"""
        self._internal_append_fixed64(data)

    def append_sfixed32(self, tag: bytes, data: int):
        """Write fixed-width 32-bit signed integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_sfixed32_without_tag(data)

    def append_sfixed32_without_tag(self, data: int):
        """Write fixed-width 32-bit signed integer without tag"""
        self.buf[self.pos:self.pos+4] = struct.pack('<i', data)
        self.pos += 4

    def append_sfixed64(self, tag: bytes, data: int):
        """Write fixed-width 64-bit signed integer with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_sfixed64_without_tag(data)

    def append_sfixed64_without_tag(self, data: int):
        """Write fixed-width 64-bit signed integer without tag"""
        self.buf[self.pos:self.pos+8] = struct.pack('<q', data)
        self.pos += 8

    def append_float32(self, tag: bytes, data: float):
        """Write 32-bit float with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_float32_without_tag(data)

    def append_float32_without_tag(self, data: float):
        """Write 32-bit float without tag"""
        self._internal_append_fixed32(struct.unpack('<I', struct.pack('<f', data))[0])

    def append_float64(self, tag: bytes, data: float):
        """Write 64-bit float with tag"""
        self.buf[self.pos:self.pos+len(tag)] = tag
        self.pos += len(tag)
        self.append_float64_without_tag(data)

    def append_float64_without_tag(self, data: float):
        """Write 64-bit float without tag"""
        self._internal_append_fixed64(struct.unpack('<Q', struct.pack('<d', data))[0])

    def append_tag(self, tag: ProtoWireNumber, wire_type: ProtoWireType):
        """Write field tag (field number and wire type)"""
        tag_varint = (tag << 3) | wire_type.value
        self.append_varint(tag_varint)

    def _internal_append_fixed32(self, v: int):
        """Write fixed 32-bit value in little-endian"""
        self.buf[self.pos:self.pos+4] = struct.pack('<I', v)
        self.pos += 4

    def _internal_append_fixed64(self, v: int):
        """Write fixed 64-bit value in little-endian"""
        self.buf[self.pos:self.pos+8] = struct.pack('<Q', v)
        self.pos += 8

    def _append_signed_varint(self, v: int):
        """Write zigzag encoded signed integer"""
        value = (v << 1) ^ (v >> 63)
        self.append_varint(value)

    def append_varint(self, v: int):
        """
        Writes a varint with unrolled loop for the most common sizes (1-5 bytes).
        Handles values up to ~34 billion without loop overhead.
        """
        # Cache attributes to local variables for fastest access
        buf = self.buf
        pos = self.pos

        if v < 0x80:
            buf[pos] = v
            self.pos = pos + 1
            return

        buf[pos] = (v & 0x7F) | 0x80
        v >>= 7
        pos += 1
        if v < 0x80:
            buf[pos] = v
            self.pos = pos + 1
            return

        buf[pos] = (v & 0x7F) | 0x80
        v >>= 7
        pos += 1
        if v < 0x80:
            buf[pos] = v
            self.pos = pos + 1
            return

        buf[pos] = (v & 0x7F) | 0x80
        v >>= 7
        pos += 1
        if v < 0x80:
            buf[pos] = v
            self.pos = pos + 1
            return

        buf[pos] = (v & 0x7F) | 0x80
        v >>= 7
        pos += 1
        if v < 0x80:
            buf[pos] = v
            self.pos = pos + 1
            return

        while True:
            buf[pos] = (v & 0x7F) | 0x80
            pos += 1
            v >>= 7
            if v < 0x80:
                buf[pos] = v
                self.pos = pos + 1
                return

    def append_raw_bytes(self, bytes_data: Union[bytes, bytearray, memoryview]):
        """Write byte slice to buffer"""
        self.buf[self.pos:self.pos+len(bytes_data)] = bytes_data
        self.pos += len(bytes_data)


class StreamingWriter:
    """Protocol buffer writer that writes directly to a stream/file."""
    
    def __init__(self, stream):
        """Initialize writer with output stream.
        
        Args:
            stream: Any object with a write(bytes) method (e.g., file handle)
        """
        self.stream = stream
        
    def reset(self):
        """Reset writer position"""
    
    def append_bytes(self, tag: bytes, data: Union[bytes, bytearray, memoryview]):
        """Write length-delimited bytes with tag"""
        self.stream.write(tag)
        
        self.append_varint(len(data))
        self.append_raw_bytes(data)
    
    def append_bytes_size_with_tag(self, tag: bytes, size: int):
        """Write length-delimited bytes with tag"""
        self.stream.write(tag)
        self.append_varint(size)
    
    def append_bytes_tag(self, tag: ProtoWireNumber, length: int):
        """Write bytes length prefix only"""
        self.append_tag(tag, ProtoWireType.BYTES)
        self.append_varint(length)
    
    def append_bool(self, tag: bytes, data: bool):
        """Write boolean value with tag"""
        self.stream.write(tag)
        self.append_bool_without_tag(data)
    
    def append_bool_without_tag(self, data: bool):
        """Write boolean value without tag"""
        self.append_varint(1 if data else 0)
    
    def append_int32(self, tag: bytes, data: int):
        """Write signed 32-bit integer with tag bytes"""
        self.stream.write(tag)
        self.append_varint(data & 0xFFFFFFFFFFFFFFFF)
    
    def append_int32_without_tag(self, data: int):
        """Write signed 32-bit integer without tag"""
        self.append_varint(data & 0xFFFFFFFFFFFFFFFF)
    
    def append_int64(self, tag: bytes, data: int):
        """Write signed 64-bit integer with tag"""
        self.stream.write(tag)
        self.append_int64_without_tag(data)
    
    def append_int64_without_tag(self, data: int):
        """Write signed 64-bit integer without tag"""
        self.append_varint(data & 0xFFFFFFFFFFFFFFFF)
    
    def append_uint32(self, tag: bytes, data: int):
        """Write unsigned 32-bit integer with tag"""
        self.stream.write(tag)
        self.append_uint32_without_tag(data)
    
    def append_uint32_without_tag(self, data: int):
        """Write unsigned 32-bit integer without tag"""
        self.append_varint(data)
    
    def append_uint64(self, tag: bytes, data: int):
        """Write unsigned 64-bit integer with tag"""
        self.stream.write(tag)
        self.append_uint64_without_tag(data)
    
    def append_uint64_without_tag(self, data: int):
        """Write unsigned 64-bit integer without tag"""
        self.append_varint(data)
    
    def append_sint32(self, tag: bytes, data: int):
        """Write zigzag encoded 32-bit integer with tag"""
        self.stream.write(tag)
        self.append_sint32_without_tag(data)
    
    def append_sint32_without_tag(self, data: int):
        """Write zigzag encoded 32-bit integer without tag"""
        self._append_signed_varint(data)
    
    def append_sint64(self, tag: bytes, data: int):
        """Write zigzag encoded 64-bit integer with tag"""
        self.stream.write(tag)
        self.append_sint64_without_tag(data)
    
    def append_sint64_without_tag(self, data: int):
        """Write zigzag encoded 64-bit integer without tag"""
        self._append_signed_varint(data)
    
    def append_fixed32(self, tag: bytes, data: int):
        """Write fixed-width 32-bit unsigned integer with tag"""
        self.stream.write(tag)
        self.append_fixed32_without_tag(data)
    
    def append_fixed32_without_tag(self, data: int):
        """Write fixed-width 32-bit unsigned integer without tag"""
        self._internal_append_fixed32(data)
    
    def append_fixed64(self, tag: bytes, data: int):
        """Write fixed-width 64-bit unsigned integer with tag"""
        self.stream.write(tag)
        self.append_fixed64_without_tag(data)
    
    def append_fixed64_without_tag(self, data: int):
        """Write fixed-width 64-bit unsigned integer without tag"""
        self._internal_append_fixed64(data)
    
    def append_sfixed32(self, tag: bytes, data: int):
        """Write fixed-width 32-bit signed integer with tag"""
        self.stream.write(tag)
        self.append_sfixed32_without_tag(data)
    
    def append_sfixed32_without_tag(self, data: int):
        """Write fixed-width 32-bit signed integer without tag"""
        self.stream.write(struct.pack('<i', data))
    
    def append_sfixed64(self, tag: bytes, data: int):
        """Write fixed-width 64-bit signed integer with tag"""
        self.stream.write(tag)
        self.append_sfixed64_without_tag(data)
    
    def append_sfixed64_without_tag(self, data: int):
        """Write fixed-width 64-bit signed integer without tag"""
        self.stream.write(struct.pack('<q', data))
    
    def append_float32(self, tag: bytes, data: float):
        """Write 32-bit float with tag"""
        self.stream.write(tag)
        self.append_float32_without_tag(data)
    
    def append_float32_without_tag(self, data: float):
        """Write 32-bit float without tag"""
        self._internal_append_fixed32(struct.unpack('<I', struct.pack('<f', data))[0])
    
    def append_float64(self, tag: bytes, data: float):
        """Write 64-bit float with tag"""
        self.stream.write(tag)
        self.append_float64_without_tag(data)
    
    def append_float64_without_tag(self, data: float):
        """Write 64-bit float without tag"""
        self._internal_append_fixed64(struct.unpack('<Q', struct.pack('<d', data))[0])
    
    def append_tag(self, tag: ProtoWireNumber, wire_type: ProtoWireType):
        """Write field tag (field number and wire type)"""
        tag_varint = (tag << 3) | wire_type.value
        self.append_varint(tag_varint)
    
    def _internal_append_fixed32(self, v: int):
        """Write fixed 32-bit value in little-endian"""
        self.stream.write(struct.pack('<I', v))
    
    def _internal_append_fixed64(self, v: int):
        """Write fixed 64-bit value in little-endian"""
        self.stream.write(struct.pack('<Q', v))
    
    def _append_signed_varint(self, v: int):
        """Write zigzag encoded signed integer"""
        value = (v << 1) ^ (v >> 63)
        self.append_varint(value)
    
    def append_varint(self, v: int):
        """Write varint directly to stream"""
        while v >= 0x80:
            self.stream.write(bytes([(v & 0x7F) | 0x80]))
            v >>= 7
        self.stream.write(bytes([v]))
    
    def append_raw_bytes(self, bytes_data: Union[bytes, bytearray, memoryview]):
        """Write byte slice directly to stream"""
        self.stream.write(bytes_data)