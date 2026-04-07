import unittest

from .buffer import ParserBuffer
from .message import Message

class MessageTest(unittest.TestCase):
    def test_basic_message(self):
        buf = ParserBuffer(
            """
            message Outer {
                option (my_option).a = true;
                message Inner {   // Level 2
                  int64 ival = 1;
                }
                map<int32, string> my_map = 2;
            }
            """
        )
        msg = Message.parse(buf, None)
        self.assertIsNotNone(msg)

        self.assertEqual("Outer", msg.name.full)
        self.assertEqual(1, len(msg.options))
        self.assertEqual("(my_option).a", msg.options[0].name)
        self.assertEqual("true", msg.options[0].value)

        self.assertEqual(1, len(msg.messages))
        self.assertEqual("Outer.Inner", msg.messages[0].name.full)
        self.assertEqual(1, len(msg.messages[0].fields))
        self.assertEqual("ival", msg.messages[0].fields[0].f_name)
        self.assertEqual(1, msg.messages[0].fields[0].index)

        self.assertEqual(1, len(msg.maps))
        self.assertEqual("my_map", msg.maps[0].f_name)
        self.assertEqual("int32", msg.maps[0].key_type)
        self.assertEqual("string", msg.maps[0].value_type.src)
        self.assertEqual(2, msg.maps[0].index)

    def test_message_with_enum(self):
        buf = ParserBuffer(
            """
            message Outer {
                enum InnerEnum {
                    VAL1 = 1;
                    VAL2 = 2;
                };
                InnerEnum usage = 1;
            }
            """
        )
        msg = Message.parse(buf, None)
        self.assertIsNotNone(msg)

        self.assertEqual("Outer", msg.name.full)
        self.assertEqual(1, len(msg.enums))
        self.assertEqual("Outer.InnerEnum", msg.enums[0].name.full)
        self.assertEqual(2, len(msg.enums[0].fields))
        self.assertEqual("VAL1", msg.enums[0].fields[0].name)
        self.assertEqual(1, msg.enums[0].fields[0].index)
        self.assertEqual("VAL2", msg.enums[0].fields[1].name)
        self.assertEqual(2, msg.enums[0].fields[1].index)

        self.assertEqual(1, len(msg.fields))
        self.assertEqual("usage", msg.fields[0].f_name)
        self.assertEqual(1, msg.fields[0].index)

    def test_just_another_message(self):
        buf = ParserBuffer(
            """
            message ConfirmEmailResponse {
              enum ConfirmEmailError {
                unknown_code = 0;
              }
              bool ok = 1;
              ConfirmEmailError error = 2;
            }
            """
        )
        msg = Message.parse(buf, None)
        self.assertIsNotNone(msg)

        self.assertEqual("ConfirmEmailResponse", msg.name.name)
        self.assertEqual(0, len(msg.options))
        self.assertEqual(0, len(msg.oneofs))
        self.assertEqual(0, len(msg.maps))
        self.assertEqual(0, len(msg.reserved))
        self.assertEqual(0, len(msg.extensions))
        self.assertEqual(1, len(msg.enums))
        self.assertEqual("ConfirmEmailResponse.ConfirmEmailError", msg.enums[0].name.full)
        self.assertEqual(1, len(msg.enums[0].fields))
        self.assertEqual("unknown_code", msg.enums[0].fields[0].name)
        self.assertEqual(0, msg.enums[0].fields[0].index)
        self.assertEqual(2, len(msg.fields))
        self.assertEqual("ok", msg.fields[0].f_name)
        self.assertEqual(1, msg.fields[0].index)
        self.assertEqual("error", msg.fields[1].f_name)
        self.assertEqual(2, msg.fields[1].index)

    def test_oneof_commas(self):
        buf = ParserBuffer(
            """
               message Outer {
                  message FieldValue {
                      oneof value {
                          string string_value = 2 [json_name = "stringValue"];
                          uint64 uint_value   = 3;
                          string datetime_value = 4;
                          bool   bool_value   = 5;
                      };
                  }
              }
            """
        )
        msg = Message.parse(buf, None)
        self.assertIsNotNone(msg)
        self.assertEqual("Outer", msg.name.full)

    def test_repeated_group(self):
        buf = ParserBuffer(
            """
          message Message3672 {
            optional .benchmarks.google_message3.Enum3476 field3727 = 1;
            optional int32 field3728 = 11;
            optional int32 field3729 = 2;
            repeated group Message3673 = 3 {
              required .benchmarks.google_message3.Enum3476 field3738 = 4;
              required int32 field3739 = 5;
            }
            repeated group Message3674 = 6 {
              required .benchmarks.google_message3.Enum3476 field3740 = 7;
              required int32 field3741 = 8;
            }
            optional bool field3732 = 9;
            optional int32 field3733 = 10;
            optional .benchmarks.google_message3.Enum3476 field3734 = 20;
            optional int32 field3735 = 21;
            optional .benchmarks.google_message3.UnusedEmptyMessage field3736 = 50;
            extend .benchmarks.google_message3.Message0 {
              optional .benchmarks.google_message3.Message3672 field3737 = 3144435;
            }
          }
            """
        )
        msg = Message.parse(buf, None)
        self.assertIsNotNone(msg)


if __name__ == "__main__":
    unittest.main()