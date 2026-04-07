import unittest
from . import sizes


class TestSizes(unittest.TestCase):

    def test_size_varint(self):
        self.assertEqual(sizes.size_varint(0), 1)
        self.assertEqual(sizes.size_varint((1 << 7) - 1), 1)
        self.assertEqual(sizes.size_varint(1 << 7), 2)
        self.assertEqual(sizes.size_varint((1 << 14) - 1), 2)
        self.assertEqual(sizes.size_varint(1 << 14), 3)
        self.assertEqual(sizes.size_varint((1 << 63) - 1), 9)
        self.assertEqual(sizes.size_varint(1 << 63), 10)

    def test_size_signed_varint(self):
        self.assertEqual(sizes.size_signed_varint(0), 1)
        self.assertEqual(sizes.size_signed_varint(-1), 1)
        self.assertEqual(sizes.size_signed_varint(1), 1)
        self.assertEqual(sizes.size_signed_varint(-2), 1)
        self.assertEqual(sizes.size_signed_varint(63), 1)
        self.assertEqual(sizes.size_signed_varint(-64), 1)
        self.assertEqual(sizes.size_signed_varint(64), 2)
        self.assertEqual(sizes.size_signed_varint(-65), 2)

    def test_size_i32(self):
        self.assertEqual(sizes.size_i32(0), 1)
        self.assertEqual(sizes.size_i32(-1), 10)
        self.assertEqual(sizes.size_i32((1 << 31) - 1), 5)
        self.assertEqual(sizes.size_i32(-(1 << 31)), 10)

    def test_size_i64(self):
        self.assertEqual(sizes.size_i64(0), 1)
        self.assertEqual(sizes.size_i64(-1), 10)
        self.assertEqual(sizes.size_i64((1 << 63) - 1), 9)
        self.assertEqual(sizes.size_i64(-(1 << 63)), 10)

    def test_size_si32(self):
        self.assertEqual(sizes.size_signed_varint(0), 1)
        self.assertEqual(sizes.size_signed_varint(-1), 1)
        self.assertEqual(sizes.size_signed_varint((1 << 31) - 1), 5)
        self.assertEqual(sizes.size_signed_varint(-(1 << 31)), 5)

    def test_size_si64(self):
        self.assertEqual(sizes.size_signed_varint(0), 1)
        self.assertEqual(sizes.size_signed_varint(-1), 1)
        self.assertEqual(sizes.size_signed_varint((1 << 63) - 1), 10)
        self.assertEqual(sizes.size_signed_varint(-(1 << 63)), 10)


if __name__ == '__main__':
    unittest.main()