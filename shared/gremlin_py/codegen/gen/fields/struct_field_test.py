import unittest
from unittest.mock import MagicMock

from ... import parser
from .struct_field import FieldBuilder
from .scalar import PythonScalarField
from .bytes import PythonBytesField
from .repeated_scalar import PythonRepeatedScalarField
from .map import PythonMapField


class TestFieldBuilder(unittest.TestCase):
    def setUp(self):
        self.fields_list = []
        self.src = parser.Message(start=0, end=0, name=parser.ScopedName("TestMessage"))
        self.scope = {"TestScope"}
        self.wire_name = "TestWire"
        self.writer_struct_name = "TestWriter"
        self.reader_struct_name = "TestReader"

    def test_create_normal_fields_scalar(self):
        field = parser.fields.NormalField(start=0, end=0, repeated=False, optional=False, required=False, f_type=None, f_name="", index=0)
        field.f_name = "test_field"
        field.f_type = parser.FieldType(src="int32", is_scalar=True, is_bytes=False, name=None, scope=parser.ScopedName(""))
        field.index = 1
        field.repeated = False
        self.src.fields.append(field)

        FieldBuilder.create_normal_fields(
            self.fields_list,
            self.src,
            self.scope,
            self.wire_name,
            self.writer_struct_name,
            self.reader_struct_name,
        )

        self.assertEqual(len(self.fields_list), 1)
        self.assertIsInstance(self.fields_list[0], PythonScalarField)

    def test_create_normal_fields_repeated_scalar(self):
        field = parser.fields.NormalField(start=0, end=0, repeated=False, optional=False, required=False, f_type=None, f_name="", index=0)
        field.f_name = "test_field"
        field.f_type = parser.FieldType(src="int32", is_scalar=True, is_bytes=False, name=None, scope=parser.ScopedName(""))
        field.index = 1
        field.repeated = True
        self.src.fields.append(field)

        FieldBuilder.create_normal_fields(
            self.fields_list,
            self.src,
            self.scope,
            self.wire_name,
            self.writer_struct_name,
            self.reader_struct_name,
        )

        self.assertEqual(len(self.fields_list), 1)
        self.assertIsInstance(self.fields_list[0], PythonRepeatedScalarField)

    def test_create_one_of_fields(self):
        oneof_field = parser.fields.OneOfField(start=0, end=0, f_type=None, f_name="", index=0)
        oneof_field.f_name = "oneof_field"
        oneof_field.f_type = parser.FieldType(src="string", is_scalar=False, is_bytes=True, name=None, scope=parser.ScopedName(""))
        oneof_field.index = 2
        oneof = MagicMock()
        oneof.fields = [oneof_field]
        self.src.oneofs.append(oneof)

        FieldBuilder.create_one_of_fields(
            self.fields_list,
            self.src,
            self.scope,
            self.wire_name,
            self.writer_struct_name,
            self.reader_struct_name,
        )

        self.assertEqual(len(self.fields_list), 1)
        self.assertIsInstance(self.fields_list[0], PythonBytesField)

    def test_create_map_fields(self):
        map_field = parser.fields.MessageMapField(start=0, end=0, key_type="", value_type=None, f_name="", index=0)
        map_field.f_name = "map_field"
        map_field.index = 3
        map_field.key_type = "string"
        map_field.value_type = parser.FieldType(src="int32", is_scalar=True, is_bytes=False, name=None, scope=parser.ScopedName(""))
        self.src.maps.append(map_field)

        FieldBuilder.create_map_fields(
            self.fields_list,
            self.src,
            self.scope,
            self.wire_name,
            self.writer_struct_name,
            self.reader_struct_name,
        )

        self.assertEqual(len(self.fields_list), 1)
        self.assertIsInstance(self.fields_list[0], PythonMapField)

    def test_create_repeated_field_unsupported(self):
        field = parser.fields.NormalField(start=0, end=0, repeated=False, optional=False, required=False, f_type=None, f_name="", index=0)
        field.f_name = "test_field"
        field.f_type = parser.FieldType(src="unknown", is_scalar=False, is_bytes=False, name=None, scope=parser.ScopedName(""))
        with self.assertRaises(TypeError):
            FieldBuilder.create_repeated_field(
                field,
                self.wire_name,
                self.scope,
                self.writer_struct_name,
                self.reader_struct_name,
            )

    def test_create_single_field_unsupported(self):
        field = parser.fields.NormalField(start=0, end=0, repeated=False, optional=False, required=False, f_type=None, f_name="", index=0)
        field.f_name = "test_field"
        field.f_type = parser.FieldType(src="unknown", is_scalar=False, is_bytes=False, name=None, scope=parser.ScopedName(""))
        with self.assertRaises(TypeError):
            FieldBuilder.create_single_field(
                field,
                self.wire_name,
                self.scope,
                self.writer_struct_name,
                self.reader_struct_name,
            )

    def test_create_one_of_field_unsupported(self):
        field = parser.fields.OneOfField(start=0, end=0, f_type=None, f_name="", index=0)
        field.f_name = "test_field"
        field.f_type = parser.FieldType(src="unknown", is_scalar=False, is_bytes=False, name=None, scope=parser.ScopedName(""))
        with self.assertRaises(TypeError):
            FieldBuilder.create_one_of_field(
                field,
                self.wire_name,
                self.scope,
                self.writer_struct_name,
                self.reader_struct_name,
            )


if __name__ == "__main__":
    unittest.main()