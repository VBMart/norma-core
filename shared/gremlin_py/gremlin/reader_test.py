import unittest
from .reader import Reader
from .types import ProtoWireType

class TestReader(unittest.TestCase):

    def test_decode_sint64(self):
        # Test decoding a specific sint64 value (106)
        data = bytes([212, 1])
        reader = Reader(data)
        result = reader.read_sint64(0)
        self.assertEqual(106, result.value)

    def test_read_negative_int64(self):
        # Expected value should be encoded as unsigned 18446744073709551584
        # Buffer should contain [8 224 255 255 255 255 255 255 255 255 1]
        expected_buf = bytes([8, 224, 255, 255, 255, 255, 255, 255, 255, 255, 1])

        # Now read it back
        reader = Reader(expected_buf)
        tag_result = reader.read_tag_at(0)
        self.assertEqual(1, tag_result.number)
        self.assertEqual(ProtoWireType.VARINT, tag_result.wire)

    def test_read_vector_of_enums(self):
        # Hex: 0a03000102
        data = bytes([0x0a, 0x03, 0x00, 0x01, 0x02])

        # Read and verify the data
        reader = Reader(data)
        offset = 0

        while offset < len(reader.bytes()):
            # Read tag
            tag = reader.read_tag_at(offset)
            offset += tag.size

            # Read bytes content
            content = reader.read_bytes(offset)
            offset += content.size

            # Verify the content is [0, 1, 2]
            self.assertEqual(bytes([0, 1, 2]), content.value)

    def test_read_bytes_view(self):
        data = bytes([0x0a, 0x03, 0x00, 0x01, 0x02])
        reader = Reader(data)
        offset = 0
        tag = reader.read_tag_at(offset)
        offset += tag.size
        content = reader.read_bytes_view(offset)
        self.assertEqual(memoryview(bytes([0, 1, 2])), content.value)


if __name__ == '__main__':
    unittest.main()