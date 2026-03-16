import sys
import os
import unittest
import struct

# The project root for import resolution during codegen
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

from codegen import generate_protobuf

def run_codegen():
    """
    Generates the protobuf Python files needed for the tests.
    """
    script_dir = os.path.dirname(__file__)
    test_data_root = os.path.join(script_dir, "test_data")
    
    target_root = os.path.join(script_dir, "gen")

    # Create __init__.py files to make the generated code importable
    if not os.path.exists(target_root):
        os.makedirs(target_root)
    with open(os.path.join(target_root, "__init__.py"), "w") as f:
        pass

    for folder in ["google", "gogofast"]:
        proto_root = os.path.join(test_data_root, folder)
        
        # Create __init__.py in subdirectories
        gen_folder = os.path.join(target_root, folder)
        if not os.path.exists(gen_folder):
            os.makedirs(gen_folder)
        with open(os.path.join(gen_folder, "__init__.py"), "w") as f:
            pass

        generate_protobuf(proto_root, gen_folder, project_root)

# Run code generation before importing the generated modules
run_codegen()

from .gen.google import unittest as unittest_pb
from .gen.google import unittest_import as unittest_import_pb
from .gen.google import unittest_import_public as unittest_import_public_pb
from .gen.google import map_test

class GremlinTests(unittest.TestCase):

    def test_simple_write(self):
        expected = bytes([
            8, 101, 16, 102, 146, 1, 2, 8, 118, 232, 3, 0, 240, 3, 0, 248, 3, 0, 128, 4, 0, 136, 4, 0, 144, 4, 0, 157,
            4, 0, 0, 0, 0, 161, 4, 0, 0, 0, 0, 0, 0, 0, 0, 173, 4, 0, 0, 0, 0, 177, 4, 0, 0, 0, 0, 0, 0, 0, 0, 189, 4,
            0, 0, 0, 0, 193, 4, 0, 0, 0, 0, 0, 0, 0, 0, 200, 4, 0, 210, 4, 0, 218, 4, 0, 136, 5, 0, 144, 5, 0, 152, 5,
            0, 162, 5, 0, 170, 5, 0
        ])

        msg = unittest_pb.TestAllTypes(
            optional_int32=101,
            optional_int64=102,
            optional_nested_message=unittest_pb.TestAllTypes_NestedMessage(bb=118),
        )

        buf = msg.encode()
        self.assertEqual(expected, buf)

    def test_simple_read(self):
        expected = bytes([
            8, 101, 16, 102, 146, 1, 2, 8, 118, 232, 3, 0, 240, 3, 0, 248, 3, 0, 128, 4, 0, 136, 4, 0, 144, 4, 0, 157,
            4, 0, 0, 0, 0, 161, 4, 0, 0, 0, 0, 0, 0, 0, 0, 173, 4, 0, 0, 0, 0, 177, 4, 0, 0, 0, 0, 0, 0, 0, 0, 189, 4,
            0, 0, 0, 0, 193, 4, 0, 0, 0, 0, 0, 0, 0, 0, 200, 4, 0, 210, 4, 0, 218, 4, 0, 136, 5, 0, 144, 5, 0, 152, 5,
            0, 162, 5, 0, 170, 5, 0
        ])

        msg = unittest_pb.TestAllTypesReader(expected)
        self.assertEqual(101, msg.get_optional_int32())
        self.assertEqual(102, msg.get_optional_int64())

        nested = msg.get_optional_nested_message()
        self.assertEqual(118, nested.get_bb())

    def test_map_kv_empty(self):
        expected = bytes([42, 4, 8, 0, 18, 0])

        msg = map_test.TestMap(
            int32_to_message_field={
                0: map_test.TestMap_MessageValue()
            }
        )

        buf = msg.encode()
        self.assertEqual(expected, buf)

        map_test.TestMapReader(buf)
        
    def test_map_kv_value(self):
        msg = map_test.TestMap(
            int32_to_message_field={
                2: map_test.TestMap_MessageValue(value=32)
            }
        )

        buf = msg.encode()

        reader = map_test.TestMapReader(buf)
        map_field = reader.get_int32_to_message_field()
        self.assertIn(2, map_field)
        self.assertEqual(32, map_field[2].get_value())

        map_field = reader.get_int32_to_message_field()
        self.assertIn(2, map_field)
        self.assertEqual(32, map_field[2].get_value())

    def test_negative_values(self):
        expected = bytes([
            8, 156, 255, 255, 255, 255, 255, 255, 255, 255, 1, 16, 155, 255, 255, 255, 255, 255, 255, 255, 255, 1, 40,
            203, 1, 48, 205, 1, 77, 152, 255, 255, 255, 81, 151, 255, 255, 255, 255, 255, 255, 255, 93, 0, 0, 210, 194,
            97, 0, 0, 0, 0, 0, 128, 90, 192, 250, 1, 20, 184, 254, 255, 255, 255, 255, 255, 255, 255, 1, 212, 253, 255,
            255, 255, 255, 255, 255, 255, 1, 130, 2, 20, 183, 254, 255, 255, 255, 255, 255, 255, 255, 1, 211, 253, 255,
            255, 255, 255, 255, 255, 255, 1, 154, 2, 4, 147, 3, 219, 4, 162, 2, 4, 149, 3, 221, 4, 186, 2, 8, 52, 255,
            255, 255, 208, 254, 255, 255, 194, 2, 16, 51, 255, 255, 255, 255, 255, 255, 255, 207, 254, 255, 255, 255,
            255, 255, 255, 202, 2, 8, 0, 0, 77, 195, 0, 128, 152, 195, 210, 2, 16, 0, 0, 0, 0, 0, 192, 105, 192, 0, 0, 0,
            0, 0, 32, 115, 192, 232, 3, 0, 240, 3, 0, 248, 3, 0, 128, 4, 0, 136, 4, 0, 144, 4, 0, 157, 4, 0, 0, 0, 0,
            161, 4, 0, 0, 0, 0, 0, 0, 0, 0, 173, 4, 0, 0, 0, 0, 177, 4, 0, 0, 0, 0, 0, 0, 0, 0, 189, 4, 0, 0, 0, 0, 193,
            4, 0, 0, 0, 0, 0, 0, 0, 0, 200, 4, 0, 210, 4, 0, 218, 4, 0, 136, 5, 0, 144, 5, 0, 152, 5, 0, 162, 5, 0, 170,
            5, 0
        ])

        msg = unittest_pb.TestAllTypes(
            optional_int32=-100,
            optional_int64=-101,
            optional_sint32=-102,
            optional_sint64=-103,
            optional_sfixed32=-104,
            optional_sfixed64=-105,
            optional_float=-105.0,
            optional_double=-106.0,
            repeated_int32=[-200, -300],
            repeated_int64=[-201, -301],
            repeated_sint32=[-202, -302],
            repeated_sint64=[-203, -303],
            repeated_sfixed32=[-204, -304],
            repeated_sfixed64=[-205, -305],
            repeated_float=[-205.0, -305.0],
            repeated_double=[-206.0, -306.0],
        )

        buf = msg.encode()
        self.assertEqual(expected, buf)

        parsed = unittest_pb.TestAllTypesReader(buf)
        self.assertEqual(-100, parsed.get_optional_int32())
        self.assertEqual(-101, parsed.get_optional_int64())
        self.assertEqual(-102, parsed.get_optional_sint32())
        self.assertEqual(-103, parsed.get_optional_sint64())
        self.assertEqual(-104, parsed.get_optional_sfixed32())
        self.assertEqual(-105, parsed.get_optional_sfixed64())
        self.assertAlmostEqual(-105.0, parsed.get_optional_float(), places=5)
        self.assertAlmostEqual(-106.0, parsed.get_optional_double(), places=5)

        self.assertEqual([-200, -300], parsed.get_repeated_int32())
        self.assertEqual([-201, -301], parsed.get_repeated_int64())
        self.assertEqual([-202, -302], parsed.get_repeated_sint32())
        self.assertEqual([-203, -303], parsed.get_repeated_sint64())
        self.assertEqual([-204, -304], parsed.get_repeated_sfixed32())
        self.assertEqual([-205, -305], parsed.get_repeated_sfixed64())
        
        for a, b in zip([-205.0, -305.0], parsed.get_repeated_float()):
            self.assertAlmostEqual(a, b, places=5)
        
        for a, b in zip([-206.0, -306.0], parsed.get_repeated_double()):
            self.assertAlmostEqual(a, b, places=5)

    def test_complex_read(self):
        expected = bytes([
            8, 101, 16, 102, 24, 103, 32, 104, 40, 210, 1, 48, 212, 1, 61, 107, 0, 0, 0, 65, 108, 0, 0, 0, 0, 0, 0, 0,
            77, 109, 0, 0, 0, 81, 110, 0, 0, 0, 0, 0, 0, 0, 93, 0, 0, 222, 66, 97, 0, 0, 0, 0, 0, 0, 92, 64, 104, 1,
            114, 3, 49, 49, 53, 122, 3, 49, 49, 54, 146, 1, 2, 8, 118, 154, 1, 2, 8, 119, 162, 1, 2, 8, 120, 168, 1, 3,
            176, 1, 6, 184, 1, 9, 194, 1, 3, 49, 50, 52, 202, 1, 3, 49, 50, 53, 210, 1, 2, 8, 126, 218, 1, 2, 8, 127,
            226, 1, 3, 8, 128, 1, 250, 1, 4, 201, 1, 173, 2, 130, 2, 4, 202, 1, 174, 2, 138, 2, 4, 203, 1, 175, 2, 146,
            2, 4, 204, 1, 176, 2, 154, 2, 4, 154, 3, 226, 4, 162, 2, 4, 156, 3, 228, 4, 170, 2, 8, 207, 0, 0, 0, 51, 1,
            0, 0, 178, 2, 16, 208, 0, 0, 0, 0, 0, 0, 0, 52, 1, 0, 0, 0, 0, 0, 0, 186, 2, 8, 209, 0, 0, 0, 53, 1, 0, 0,
            194, 2, 16, 210, 0, 0, 0, 0, 0, 0, 0, 54, 1, 0, 0, 0, 0, 0, 0, 202, 2, 8, 0, 0, 83, 67, 0, 128, 155, 67,
            210, 2, 16, 0, 0, 0, 0, 0, 128, 106, 64, 0, 0, 0, 0, 0, 128, 115, 64, 218, 2, 2, 1, 0, 226, 2, 3, 50, 49,
            53, 226, 2, 3, 51, 49, 53, 234, 2, 3, 50, 49, 54, 234, 2, 3, 51, 49, 54, 130, 3, 3, 8, 218, 1, 130, 3, 3, 8,
            190, 2, 138, 3, 3, 8, 219, 1, 138, 3, 3, 8, 191, 2, 146, 3, 3, 8, 220, 1, 146, 3, 3, 8, 192, 2, 154, 3, 2,
            2, 3, 162, 3, 2, 5, 6, 170, 3, 2, 8, 9, 178, 3, 3, 50, 50, 52, 178, 3, 3, 51, 50, 52, 186, 3, 3, 50, 50, 53,
            186, 3, 3, 51, 50, 53, 202, 3, 3, 8, 227, 1, 202, 3, 3, 8, 199, 2, 232, 3, 145, 3, 240, 3, 146, 3, 248, 3,
            147, 3, 128, 4, 148, 3, 136, 4, 170, 6, 144, 4, 172, 6, 157, 4, 151, 1, 0, 0, 161, 4, 152, 1, 0, 0, 0, 0, 0,
            0, 173, 4, 153, 1, 0, 0, 177, 4, 154, 1, 0, 0, 0, 0, 0, 0, 189, 4, 0, 128, 205, 67, 193, 4, 0, 0, 0, 0, 0,
            192, 121, 64, 200, 4, 0, 210, 4, 3, 52, 49, 53, 218, 4, 3, 52, 49, 54, 136, 5, 1, 144, 5, 4, 152, 5, 7, 162,
            5, 3, 52, 50, 52, 170, 5, 3, 52, 50, 53, 248, 6, 217, 4
        ])

        msg = unittest_pb.TestAllTypesReader(expected)

        self.assertEqual(101, msg.get_optional_int32())
        self.assertEqual(102, msg.get_optional_int64())
        self.assertEqual(103, msg.get_optional_uint32())
        self.assertEqual(104, msg.get_optional_uint64())
        self.assertEqual(105, msg.get_optional_sint32())
        self.assertEqual(106, msg.get_optional_sint64())
        self.assertEqual(107, msg.get_optional_fixed32())
        self.assertEqual(108, msg.get_optional_fixed64())
        self.assertEqual(109, msg.get_optional_sfixed32())
        self.assertEqual(110, msg.get_optional_sfixed64())
        self.assertAlmostEqual(111.0, msg.get_optional_float(), places=5)
        self.assertAlmostEqual(112.0, msg.get_optional_double(), places=5)
        self.assertEqual(True, msg.get_optional_bool())
        self.assertEqual("115", msg.get_optional_string())
        self.assertEqual(b"116", msg.get_optional_bytes())

        nested = msg.get_optional_nested_message()
        self.assertEqual(118, nested.get_bb())

        foreign = msg.get_optional_foreign_message()
        self.assertEqual(119, foreign.get_c())

        import_msg = msg.get_optional_import_message()
        self.assertEqual(120, import_msg.get_d())

        self.assertEqual([201, 301], msg.get_repeated_int32())

        self.assertEqual(unittest_pb.TestAllTypes_NestedEnum.BAZ, msg.get_optional_nested_enum())
        self.assertEqual(unittest_pb.ForeignEnum.FOREIGN_BAZ, msg.get_optional_foreign_enum())
        self.assertEqual(unittest_import_pb.ImportEnum.IMPORT_BAZ, msg.get_optional_import_enum())

        self.assertEqual("124", msg.get_optional_string_piece())
        self.assertEqual("125", msg.get_optional_cord())

        self.assertEqual(401, msg.get_default_int32())
        self.assertEqual(402, msg.get_default_int64())
        self.assertEqual(403, msg.get_default_uint32())
        self.assertEqual(404, msg.get_default_uint64())
        self.assertEqual(False, msg.get_default_bool())
        self.assertEqual("415", msg.get_default_string())
        self.assertEqual(b"416", msg.get_default_bytes())

        self.assertEqual(601, msg.get_oneof_uint32())

    def test_complex_write(self):
        expected = bytes([
            8, 101, 16, 102, 24, 103, 32, 104, 40, 210, 1, 48, 212, 1, 61, 107, 0, 0, 0, 65, 108, 0, 0, 0, 0, 0, 0, 0,
            77, 109, 0, 0, 0, 81, 110, 0, 0, 0, 0, 0, 0, 0, 93, 0, 0, 222, 66, 97, 0, 0, 0, 0, 0, 0, 92, 64, 104, 1,
            114, 3, 49, 49, 53, 122, 3, 49, 49, 54, 146, 1, 2, 8, 118, 154, 1, 2, 8, 119, 162, 1, 2, 8, 120, 168, 1, 3,
            176, 1, 6, 184, 1, 9, 194, 1, 3, 49, 50, 52, 202, 1, 3, 49, 50, 53, 210, 1, 2, 8, 126, 218, 1, 2, 8, 127,
            226, 1, 3, 8, 128, 1, 250, 1, 4, 201, 1, 173, 2, 130, 2, 4, 202, 1, 174, 2, 138, 2, 4, 203, 1, 175, 2, 146,
            2, 4, 204, 1, 176, 2, 154, 2, 4, 154, 3, 226, 4, 162, 2, 4, 156, 3, 228, 4, 170, 2, 8, 207, 0, 0, 0, 51, 1,
            0, 0, 178, 2, 16, 208, 0, 0, 0, 0, 0, 0, 0, 52, 1, 0, 0, 0, 0, 0, 0, 186, 2, 8, 209, 0, 0, 0, 53, 1, 0, 0,
            194, 2, 16, 210, 0, 0, 0, 0, 0, 0, 0, 54, 1, 0, 0, 0, 0, 0, 0, 202, 2, 8, 0, 0, 83, 67, 0, 128, 155, 67,
            210, 2, 16, 0, 0, 0, 0, 0, 128, 106, 64, 0, 0, 0, 0, 0, 128, 115, 64, 218, 2, 2, 1, 0, 226, 2, 3, 50, 49,
            53, 226, 2, 3, 51, 49, 53, 234, 2, 3, 50, 49, 54, 234, 2, 3, 51, 49, 54, 130, 3, 3, 8, 218, 1, 130, 3, 3, 8,
            190, 2, 138, 3, 3, 8, 219, 1, 138, 3, 3, 8, 191, 2, 146, 3, 3, 8, 220, 1, 146, 3, 3, 8, 192, 2, 154, 3, 2,
            2, 3, 162, 3, 2, 5, 6, 170, 3, 2, 8, 9, 178, 3, 3, 50, 50, 52, 178, 3, 3, 51, 50, 52, 186, 3, 3, 50, 50, 53,
            186, 3, 3, 51, 50, 53, 202, 3, 3, 8, 227, 1, 202, 3, 3, 8, 199, 2, 232, 3, 145, 3, 240, 3, 146, 3, 248, 3,
            147, 3, 128, 4, 148, 3, 136, 4, 170, 6, 144, 4, 172, 6, 157, 4, 151, 1, 0, 0, 161, 4, 152, 1, 0, 0, 0, 0, 0,
            0, 173, 4, 153, 1, 0, 0, 177, 4, 154, 1, 0, 0, 0, 0, 0, 0, 189, 4, 0, 128, 205, 67, 193, 4, 0, 0, 0, 0, 0,
            192, 121, 64, 200, 4, 0, 210, 4, 3, 52, 49, 53, 218, 4, 3, 52, 49, 54, 136, 5, 1, 144, 5, 4, 152, 5, 7, 162,
            5, 3, 52, 50, 52, 170, 5, 3, 52, 50, 53, 248, 6, 217, 4
        ])

        msg = unittest_pb.TestAllTypes(
            optional_int32=101,
            optional_int64=102,
            optional_uint32=103,
            optional_uint64=104,
            optional_sint32=105,
            optional_sint64=106,
            optional_fixed32=107,
            optional_fixed64=108,
            optional_sfixed32=109,
            optional_sfixed64=110,
            optional_float=111.0,
            optional_double=112.0,
            optional_bool=True,
            optional_string="115",
            optional_bytes=b"116",
            optional_nested_message=unittest_pb.TestAllTypes_NestedMessage(bb=118),
            optional_foreign_message=unittest_pb.ForeignMessage(c=119),
            optional_import_message=unittest_import_pb.ImportMessage(d=120),
            optional_public_import_message=unittest_import_public_pb.PublicImportMessage(e=126),
            optional_lazy_message=unittest_pb.TestAllTypes_NestedMessage(bb=127),
            optional_unverified_lazy_message=unittest_pb.TestAllTypes_NestedMessage(bb=128),
            optional_nested_enum=unittest_pb.TestAllTypes_NestedEnum.BAZ,
            optional_foreign_enum=unittest_pb.ForeignEnum.FOREIGN_BAZ,
            optional_import_enum=unittest_import_pb.ImportEnum.IMPORT_BAZ,
            optional_string_piece="124",
            optional_cord="125",
            repeated_int32=[201, 301],
            repeated_int64=[202, 302],
            repeated_uint32=[203, 303],
            repeated_uint64=[204, 304],
            repeated_sint32=[205, 305],
            repeated_sint64=[206, 306],
            repeated_fixed32=[207, 307],
            repeated_fixed64=[208, 308],
            repeated_sfixed32=[209, 309],
            repeated_sfixed64=[210, 310],
            repeated_float=[211.0, 311.0],
            repeated_double=[212.0, 312.0],
            repeated_bool=[True, False],
            repeated_string=["215", "315"],
            repeated_bytes=[b"216", b"316"],
            repeated_nested_message=[
                unittest_pb.TestAllTypes_NestedMessage(bb=218),
                unittest_pb.TestAllTypes_NestedMessage(bb=318),
            ],
            repeated_foreign_message=[
                unittest_pb.ForeignMessage(c=219),
                unittest_pb.ForeignMessage(c=319),
            ],
            repeated_import_message=[
                unittest_import_pb.ImportMessage(d=220),
                unittest_import_pb.ImportMessage(d=320),
            ],
            repeated_lazy_message=[
                unittest_pb.TestAllTypes_NestedMessage(bb=227),
                unittest_pb.TestAllTypes_NestedMessage(bb=327),
            ],
            repeated_nested_enum=[
                unittest_pb.TestAllTypes_NestedEnum.BAR,
                unittest_pb.TestAllTypes_NestedEnum.BAZ,
            ],
            repeated_foreign_enum=[
                unittest_pb.ForeignEnum.FOREIGN_BAR,
                unittest_pb.ForeignEnum.FOREIGN_BAZ,
            ],
            repeated_import_enum=[
                unittest_import_pb.ImportEnum.IMPORT_BAR,
                unittest_import_pb.ImportEnum.IMPORT_BAZ,
            ],
            repeated_string_piece=["224", "324"],
            repeated_cord=["225", "325"],
            default_int32=401,
            default_int64=402,
            default_uint32=403,
            default_uint64=404,
            default_sint32=405,
            default_sint64=406,
            default_fixed32=407,
            default_fixed64=408,
            default_sfixed32=409,
            default_sfixed64=410,
            default_float=411.0,
            default_double=412.0,
            default_bool=False,
            default_string="415",
            default_bytes=b"416",
            default_nested_enum=unittest_pb.TestAllTypes_NestedEnum.FOO,
            default_foreign_enum=unittest_pb.ForeignEnum.FOREIGN_FOO,
            default_import_enum=unittest_import_pb.ImportEnum.IMPORT_FOO,
            default_string_piece="424",
            default_cord="425",
            oneof_uint32=601,
        )
        buf = msg.encode()
        self.assertEqual(expected, buf)

    def test_nil_list(self):
        expected = bytes([
            202, 3, 0, 202, 3, 2, 8, 1, 202, 3, 0, 232, 3, 0, 240, 3, 0, 248, 3, 0, 128, 4, 0, 136, 4, 0, 144, 4, 0,
            157, 4, 0, 0, 0, 0, 161, 4, 0, 0, 0, 0, 0, 0, 0, 0, 173, 4, 0, 0, 0, 0, 177, 4, 0, 0, 0, 0, 0, 0, 0, 0, 189,
            4, 0, 0, 0, 0, 193, 4, 0, 0, 0, 0, 0, 0, 0, 0, 200, 4, 0, 210, 4, 0, 218, 4, 0, 136, 5, 0, 144, 5, 0, 152,
            5, 0, 162, 5, 0, 170, 5, 0
        ])

        msg = unittest_pb.TestAllTypes(
            repeated_lazy_message=[
                None,
                unittest_pb.TestAllTypes_NestedMessage(bb=1),
                None,
            ]
        )

        buf = msg.encode()
        self.assertEqual(expected, buf)
    
    def test_map_parsing(self):
        file_path = os.path.join(os.path.dirname(__file__), "binaries", "map_test")
        with open(file_path, "rb") as f:
            content = f.read()

        data = map_test.TestMapReader(content)

        # Test int32 to int32 map
        map_field = data.get_int32_to_int32_field()
        self.assertEqual(101, map_field[100])
        self.assertEqual(201, map_field[200])

        # Test int32 to string map
        map_field = data.get_int32_to_string_field()
        self.assertEqual("101", map_field[101])
        self.assertEqual("201", map_field[201])

        # Test int32 to enum map
        map_field = data.get_int32_to_enum_field()
        self.assertEqual(map_test.TestMap_EnumValue.FOO, map_field[103])
        self.assertEqual(map_test.TestMap_EnumValue.BAR, map_field[203])

        # Test string to int32 map
        map_field = data.get_string_to_int32_field()
        self.assertEqual(105, map_field["105"])
        self.assertEqual(205, map_field["205"])

        # Test uint32 to int32 map
        map_field = data.get_uint32_to_int32_field()
        self.assertEqual(106, map_field[106])
        self.assertEqual(206, map_field[206])

        # Test int64 to int32 map
        map_field = data.get_int64_to_int32_field()
        self.assertEqual(107, map_field[107])
        self.assertEqual(207, map_field[207])

        # Test int32 to message map
        map_field = data.get_int32_to_message_field()
        msg1 = map_field[104]
        self.assertEqual(104, msg1.get_value())
        msg2 = map_field[204]
        self.assertEqual(204, msg2.get_value())

    def test_golden_message(self):
        file_path = os.path.join(os.path.dirname(__file__), "binaries", "golden_message")
        with open(file_path, "rb") as f:
            content = f.read()

        parsed = unittest_pb.TestAllTypesReader(content)

        self.assertEqual(101, parsed.get_optional_int32())
        self.assertEqual(102, parsed.get_optional_int64())
        self.assertEqual(103, parsed.get_optional_uint32())
        self.assertEqual(104, parsed.get_optional_uint64())
        self.assertEqual(105, parsed.get_optional_sint32())
        self.assertEqual(106, parsed.get_optional_sint64())
        self.assertEqual(107, parsed.get_optional_fixed32())
        self.assertEqual(108, parsed.get_optional_fixed64())
        self.assertEqual(109, parsed.get_optional_sfixed32())
        self.assertEqual(110, parsed.get_optional_sfixed64())
        self.assertAlmostEqual(111.0, parsed.get_optional_float(), places=5)
        self.assertAlmostEqual(112.0, parsed.get_optional_double(), places=5)
        self.assertEqual(True, parsed.get_optional_bool())
        self.assertEqual("115", parsed.get_optional_string())
        self.assertEqual(b"116", parsed.get_optional_bytes())

        nested = parsed.get_optional_nested_message()
        self.assertEqual(118, nested.get_bb())

        foreign = parsed.get_optional_foreign_message()
        self.assertEqual(119, foreign.get_c())

        import_msg = parsed.get_optional_import_message()
        self.assertEqual(120, import_msg.get_d())

        public_import = parsed.get_optional_public_import_message()
        self.assertEqual(126, public_import.get_e())

        lazy = parsed.get_optional_lazy_message()
        self.assertEqual(127, lazy.get_bb())

        unverified = parsed.get_optional_unverified_lazy_message()
        self.assertEqual(128, unverified.get_bb())

        self.assertEqual(unittest_pb.TestAllTypes_NestedEnum.BAZ, parsed.get_optional_nested_enum())
        self.assertEqual(unittest_pb.ForeignEnum.FOREIGN_BAZ, parsed.get_optional_foreign_enum())
        self.assertEqual(unittest_import_pb.ImportEnum.IMPORT_BAZ, parsed.get_optional_import_enum())

        self.assertEqual("124", parsed.get_optional_string_piece())
        self.assertEqual("125", parsed.get_optional_cord())

        self.assertEqual([201, 301], parsed.get_repeated_int32())
        self.assertEqual([202, 302], parsed.get_repeated_int64())

        self.assertEqual(601, parsed.get_oneof_uint32())

        msg = parsed.get_oneof_nested_message()
        self.assertEqual(602, msg.get_bb())

        self.assertEqual("603", parsed.get_oneof_string())
        self.assertEqual(b"604", parsed.get_oneof_bytes())

    def test_repeated_types_marshal_and_parse(self):
        msg = unittest_pb.TestAllTypes(
            repeated_int32=[-42, 0, 42],
            repeated_int64=[-9223372036854775808, 0, 9223372036854775807],
            repeated_uint32=[0, 42, 4294967295],
            repeated_uint64=[0, 42, 18446744073709551615],
            repeated_sint32=[-2147483648, 0, 2147483647],
            repeated_sint64=[-9223372036854775808, 0, 9223372036854775807],
            repeated_fixed32=[0, 42, 4294967295],
            repeated_fixed64=[0, 42, 18446744073709551615],
            repeated_sfixed32=[-2147483648, 0, 2147483647],
            repeated_sfixed64=[-9223372036854775808, 0, 9223372036854775807],
            repeated_float=[-3.4028235e+38, 0, 3.4028235e+38],
            repeated_double=[-1.7976931348623157e+308, 0, 1.7976931348623157e+308],
            repeated_bool=[True, False, True],
            repeated_string=["hello", "", "world"],
            repeated_bytes=[b"bytes1", b"", b"bytes2"],
            repeated_nested_message=[
                unittest_pb.TestAllTypes_NestedMessage(bb=1),
                unittest_pb.TestAllTypes_NestedMessage(bb=2),
                unittest_pb.TestAllTypes_NestedMessage(bb=3),
            ],
            repeated_nested_enum=[
                unittest_pb.TestAllTypes_NestedEnum.FOO,
                unittest_pb.TestAllTypes_NestedEnum.BAR,
                unittest_pb.TestAllTypes_NestedEnum.BAZ,
            ],
            repeated_string_piece=["piece1", "", "piece2"],
            repeated_cord=["cord1", "", "cord2"],
        )

        buf = msg.encode()
        parsed = unittest_pb.TestAllTypesReader(buf)

        self.assertEqual(msg.repeated_int32, parsed.get_repeated_int32())
        self.assertEqual(msg.repeated_int64, parsed.get_repeated_int64())
        self.assertEqual(msg.repeated_uint32, parsed.get_repeated_uint32())
        self.assertEqual(msg.repeated_uint64, parsed.get_repeated_uint64())
        self.assertEqual(msg.repeated_sint32, parsed.get_repeated_sint32())
        self.assertEqual(msg.repeated_sint64, parsed.get_repeated_sint64())
        self.assertEqual(msg.repeated_fixed32, parsed.get_repeated_fixed32())
        self.assertEqual(msg.repeated_fixed64, parsed.get_repeated_fixed64())
        self.assertEqual(msg.repeated_sfixed32, parsed.get_repeated_sfixed32())
        self.assertEqual(msg.repeated_sfixed64, parsed.get_repeated_sfixed64())

        expected_floats = [struct.unpack('<f', struct.pack('<f', v))[0] for v in msg.repeated_float]
        for a, b in zip(expected_floats, parsed.get_repeated_float()):
            self.assertAlmostEqual(a, b, places=5)
        
        for a, b in zip(msg.repeated_double, parsed.get_repeated_double()):
            self.assertAlmostEqual(a, b, places=3)

        self.assertEqual(msg.repeated_bool, parsed.get_repeated_bool())
        self.assertEqual(msg.repeated_string, parsed.get_repeated_string())
        self.assertEqual(msg.repeated_bytes, parsed.get_repeated_bytes())

        parsed_nested = parsed.get_repeated_nested_message()
        self.assertEqual(len(msg.repeated_nested_message), len(parsed_nested))
        for a, b in zip(msg.repeated_nested_message, parsed_nested):
            self.assertEqual(a.bb, b.get_bb())

        self.assertEqual(msg.repeated_nested_enum, parsed.get_repeated_nested_enum())
        self.assertEqual(msg.repeated_string_piece, parsed.get_repeated_string_piece())
        self.assertEqual(msg.repeated_cord, parsed.get_repeated_cord())


if __name__ == '__main__':
    unittest.main()