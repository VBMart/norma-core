import unittest
from .buffer import ParserBuffer
from .extend import Extend, ExtendField

class ExtendTest(unittest.TestCase):
    def test_extend_field_parsing(self):
        buf = ParserBuffer("string field = 0;")
        result = ExtendField.parse(buf)
        
        self.assertIsNotNone(result)
        self.assertEqual(0, result.start)
        self.assertEqual(17, result.end)
        self.assertEqual("string", result.f_type)
        self.assertEqual("field", result.f_name)
        self.assertEqual("0", result.f_value)

    def test_extend_block_parsing(self):
        buf = ParserBuffer(
            """
            extend TestUnpackedExtensions {
                repeated    int32 unpacked_int32_extension    =  90 [packed = false];
                repeated    int64 unpacked_int64_extension    =  91 [packed = false];
                repeated   uint32 unpacked_uint32_extension   =  92 [packed = false];
                repeated   uint64 unpacked_uint64_extension   =  93 [packed = false];
                repeated   sint32 unpacked_sint32_extension   =  94 [packed = false];
                repeated   sint64 unpacked_sint64_extension   =  95 [packed = false];
                repeated  fixed32 unpacked_fixed32_extension  =  96 [packed = false];
                repeated  fixed64 unpacked_fixed64_extension  =  97 [packed = false];
                repeated sfixed32 unpacked_sfixed32_extension =  98 [packed = false];
                repeated sfixed64 unpacked_sfixed64_extension =  99 [packed = false];
                repeated    float unpacked_float_extension    = 100 [packed = false];
                repeated   double unpacked_double_extension   = 101 [packed = false];
                repeated     bool unpacked_bool_extension     = 102 [packed = false];
                repeated ForeignEnum unpacked_enum_extension  = 103 [packed = false];
            }
            """
        )
        result = Extend.parse(buf)
        self.assertIsNotNone(result)
        self.assertEqual(result.base.full, "TestUnpackedExtensions")
        self.assertEqual(len(result.fields), 14)

if __name__ == '__main__':
    unittest.main()