import unittest
from .buffer import ParserBuffer
from .service import Service
from .errors import ProtoError, ParsingError

class ServiceTest(unittest.TestCase):
    def test_service_parsing(self):
        # Test case 1: Not a service definition
        buf = ParserBuffer("message Test {}")
        self.assertIsNone(Service.parse(buf))

        # Test case 2: Simple empty service
        buf = ParserBuffer("service Test {}")
        result = Service.parse(buf)
        self.assertIsNotNone(result)

        # Test case 3: Service with nested braces
        buf = ParserBuffer(
            "service Test {\n"
            "    rpc Method1 (Request) { option deprecated = true; }\n"
            "    rpc Method2 (Request) returns (Response) { option idempotency_level = \"NO_SIDE_EFFECTS\"; }\n"
            "}"
        )
        result = Service.parse(buf)
        self.assertIsNotNone(result)

        # Test case 4: Invalid brace matching
        with self.assertRaises(ProtoError) as cm:
            buf = ParserBuffer("service Test {{}")
            Service.parse(buf)
        self.assertEqual(cm.exception.error_code, ParsingError.UnexpectedEOF)

        # Test case 5: Unexpected EOF
        with self.assertRaises(ProtoError) as cm:
            buf = ParserBuffer("service Test {")
            Service.parse(buf)
        self.assertEqual(cm.exception.error_code, ParsingError.UnexpectedEOF)

if __name__ == '__main__':
    unittest.main()