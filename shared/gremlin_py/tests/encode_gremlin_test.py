"""
Test for protobuf serialization (marshalling) of TestAllTypes.
Creates protobuf messages and verifies their serialization.

This module can be used both as a unittest test suite and with timeit for performance benchmarking.

Usage (run from shared/gremlin_py/ directory):
    # Run all tests
    python3 -m unittest tests.encode_gremlin_test

    # Run built-in benchmarks
    python3 -m tests.encode_gremlin_test --benchmark

    # Run specific test
    python3 -m unittest tests.encode_gremlin_test.TestProtobufMarshalling.test_huge_test_all_types_serialization

    # Use with timeit for custom benchmarking
    python3 -m timeit -s "from tests.encode_gremlin_test import setup_huge_message, benchmark_serialize_huge; setup_huge_message()" "benchmark_serialize_huge()"
"""

import unittest
import timeit
import random

from tests.gen.google import unittest as unittest_pb
from tests.gen.google import unittest_import
from tests.gen.google import unittest_import_public


# ============================================================================
# Message Creation Functions
# ============================================================================

def create_huge_test_all_types():
    """
    Create a fully populated TestAllTypes message with all fields filled.
    Uses the custom protobuf implementation with random values.
    """
    # Create nested messages with random values
    nested_message = unittest_pb.TestAllTypes_NestedMessage(
        bb=random.randint(0, 1000000)
    )

    foreign_message = unittest_pb.ForeignMessage(
        c=random.randint(0, 1000000),
        d=random.randint(0, 1000000)
    )

    import_message = unittest_import.ImportMessage(
        d=random.randint(0, 1000000)
    )

    public_import_message = unittest_import_public.PublicImportMessage(
        e=random.randint(0, 1000000)
    )

    # Create repeated nested messages with random values
    repeated_nested_messages = [
        unittest_pb.TestAllTypes_NestedMessage(bb=random.randint(0, 1000000))
        for _ in range(50)
    ]

    repeated_foreign_messages = [
        unittest_pb.ForeignMessage(c=random.randint(0, 1000000), d=random.randint(0, 1000000))
        for _ in range(50)
    ]

    repeated_import_messages = [
        unittest_import.ImportMessage(d=random.randint(0, 1000000))
        for _ in range(50)
    ]

    # Create the huge TestAllTypes message with ALL fields populated with random values
    msg = unittest_pb.TestAllTypes(
        # Optional scalar fields - integers
        optional_int32=random.randint(-2147483648, 2147483647),
        optional_int64=random.randint(-9223372036854775808, 9223372036854775807),
        optional_uint32=random.randint(0, 4294967295),
        optional_uint64=random.randint(0, 18446744073709551615),
        optional_sint32=random.randint(-2147483648, 2147483647),
        optional_sint64=random.randint(-9223372036854775808, 9223372036854775807),
        optional_fixed32=random.randint(0, 4294967295),
        optional_fixed64=random.randint(0, 18446744073709551615),
        optional_sfixed32=random.randint(-2147483648, 2147483647),
        optional_sfixed64=random.randint(-9223372036854775808, 9223372036854775807),

        # Optional scalar fields - floats
        optional_float=random.uniform(-1e10, 1e10),
        optional_double=random.uniform(-1e100, 1e100),

        # Optional scalar fields - bool and strings
        optional_bool=random.choice([True, False]),
        optional_string="".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=460)),
        optional_bytes=bytes(random.randint(0, 255) for _ in range(1024)),

        # Optional message fields
        optional_nested_message=nested_message,
        optional_foreign_message=foreign_message,
        optional_import_message=import_message,
        optional_public_import_message=public_import_message,
        optional_lazy_message=unittest_pb.TestAllTypes_NestedMessage(bb=random.randint(0, 1000000)),
        optional_unverified_lazy_message=unittest_pb.TestAllTypes_NestedMessage(bb=random.randint(0, 1000000)),

        # Optional enum fields
        optional_nested_enum=random.choice([
            unittest_pb.TestAllTypes_NestedEnum.FOO,
            unittest_pb.TestAllTypes_NestedEnum.BAR,
            unittest_pb.TestAllTypes_NestedEnum.BAZ,
            unittest_pb.TestAllTypes_NestedEnum.NEG,
        ]),
        optional_foreign_enum=random.choice([
            unittest_pb.ForeignEnum.FOREIGN_FOO,
            unittest_pb.ForeignEnum.FOREIGN_BAR,
            unittest_pb.ForeignEnum.FOREIGN_BAZ,
        ]),
        optional_import_enum=random.choice([
            unittest_import.ImportEnum.IMPORT_FOO,
            unittest_import.ImportEnum.IMPORT_BAR,
            unittest_import.ImportEnum.IMPORT_BAZ,
        ]),

        # Optional string piece and cord
        optional_string_piece="".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=1000)),
        optional_cord="".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=1000)),

        # Repeated scalar fields - integers (large arrays)
        repeated_int32=[random.randint(-2147483648, 2147483647) for _ in range(2000)],
        repeated_int64=[random.randint(-9223372036854775808, 9223372036854775807) for _ in range(10000)],
        repeated_uint32=[random.randint(0, 4294967295) for _ in range(2000)],
        repeated_uint64=[random.randint(0, 18446744073709551615) for _ in range(2000)],
        repeated_sint32=[random.randint(-2147483648, 2147483647) for _ in range(2000)],
        repeated_sint64=[random.randint(-9223372036854775808, 9223372036854775807) for _ in range(2000)],
        repeated_fixed32=[random.randint(0, 4294967295) for _ in range(500)],
        repeated_fixed64=[random.randint(0, 18446744073709551615) for _ in range(500)],
        repeated_sfixed32=[random.randint(-2147483648, 2147483647) for _ in range(1000)],
        repeated_sfixed64=[random.randint(-9223372036854775808, 9223372036854775807) for _ in range(1000)],

        # Repeated scalar fields - floats
        repeated_float=[random.uniform(-1e10, 1e10) for _ in range(1000)],
        repeated_double=[random.uniform(-1e100, 1e100) for _ in range(1000)],

        # Repeated scalar fields - bool and strings
        repeated_bool=[random.choice([True, False]) for _ in range(100)],
        repeated_string=["".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=20)) for _ in range(100)],
        repeated_bytes=[bytes(random.randint(0, 255) for _ in range(10)) for _ in range(100)],

        # Repeated message fields
        repeated_nested_message=repeated_nested_messages,
        repeated_foreign_message=repeated_foreign_messages,
        repeated_import_message=repeated_import_messages,
        repeated_lazy_message=[
            unittest_pb.TestAllTypes_NestedMessage(bb=random.randint(0, 1000000))
            for _ in range(20)
        ],

        # Repeated enum fields
        repeated_nested_enum=[
            random.choice([
                unittest_pb.TestAllTypes_NestedEnum.FOO,
                unittest_pb.TestAllTypes_NestedEnum.BAR,
                unittest_pb.TestAllTypes_NestedEnum.BAZ,
                unittest_pb.TestAllTypes_NestedEnum.NEG,
            ])
            for _ in range(100)
        ],
        repeated_foreign_enum=[
            random.choice([
                unittest_pb.ForeignEnum.FOREIGN_FOO,
                unittest_pb.ForeignEnum.FOREIGN_BAR,
                unittest_pb.ForeignEnum.FOREIGN_BAZ,
            ])
            for _ in range(90)
        ],
        repeated_import_enum=[
            random.choice([
                unittest_import.ImportEnum.IMPORT_FOO,
                unittest_import.ImportEnum.IMPORT_BAR,
                unittest_import.ImportEnum.IMPORT_BAZ,
            ])
            for _ in range(90)
        ],

        # Repeated string piece and cord
        repeated_string_piece=["".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=30)) for _ in range(50)],
        repeated_cord=["".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=30)) for _ in range(50)],

        # Default fields (with non-default values)
        default_int32=random.randint(-2147483648, 2147483647),
        default_int64=random.randint(-9223372036854775808, 9223372036854775807),
        default_uint32=random.randint(0, 4294967295),
        default_uint64=random.randint(0, 18446744073709551615),
        default_sint32=random.randint(-2147483648, 2147483647),
        default_sint64=random.randint(-9223372036854775808, 9223372036854775807),
        default_fixed32=random.randint(0, 4294967295),
        default_fixed64=random.randint(0, 18446744073709551615),
        default_sfixed32=random.randint(-2147483648, 2147483647),
        default_sfixed64=random.randint(-9223372036854775808, 9223372036854775807),
        default_float=random.uniform(-1e10, 1e10),
        default_double=random.uniform(-1e100, 1e100),
        default_bool=random.choice([True, False]),
        default_string="".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=740)),
        default_bytes=bytes(random.randint(0, 255) for _ in range(600)),
        default_nested_enum=random.choice([
            unittest_pb.TestAllTypes_NestedEnum.FOO,
            unittest_pb.TestAllTypes_NestedEnum.BAR,
            unittest_pb.TestAllTypes_NestedEnum.BAZ,
            unittest_pb.TestAllTypes_NestedEnum.NEG,
        ]),
        default_foreign_enum=random.choice([
            unittest_pb.ForeignEnum.FOREIGN_FOO,
            unittest_pb.ForeignEnum.FOREIGN_BAR,
            unittest_pb.ForeignEnum.FOREIGN_BAZ,
        ]),
        default_import_enum=random.choice([
            unittest_import.ImportEnum.IMPORT_FOO,
            unittest_import.ImportEnum.IMPORT_BAR,
            unittest_import.ImportEnum.IMPORT_BAZ,
        ]),
        default_string_piece="".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=50)),
        default_cord="".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=50)),

        # Oneof fields (using oneof_string as an example)
        oneof_string="".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=540)),
    )

    return msg


def create_nested_test_all_types(max_depth=10):
    """
    Create a deeply nested NestedTestAllTypes structure with random values.
    """
    def create_nested(depth, max_depth):
        if depth >= max_depth:
            return None

        return unittest_pb.NestedTestAllTypes(
            child=create_nested(depth + 1, max_depth),
            payload=unittest_pb.TestAllTypes(
                optional_int32=random.randint(-2147483648, 2147483647),
                optional_string="".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=100)),
                repeated_int32=[random.randint(-2147483648, 2147483647) for _ in range(depth * 10)],
            ),
            repeated_child=[
                unittest_pb.NestedTestAllTypes(
                    payload=unittest_pb.TestAllTypes(
                        optional_int32=random.randint(-2147483648, 2147483647),
                    )
                )
                for _ in range(5)
            ]
        )

    return create_nested(0, max_depth)


def create_empty_test_all_types():
    """Create an empty TestAllTypes message."""
    return unittest_pb.TestAllTypes()


# ============================================================================
# Benchmark Functions (for timeit)
# ============================================================================

# Pre-created messages for benchmarking (created once, reused for timing)
_huge_message = None
_nested_message = None
_empty_message = None


def setup_huge_message():
    """Setup function for timeit - creates the huge message once."""
    global _huge_message
    _huge_message = create_huge_test_all_types()


def setup_nested_message():
    """Setup function for timeit - creates the nested message once."""
    global _nested_message
    _nested_message = create_nested_test_all_types()


def setup_empty_message():
    """Setup function for timeit - creates the empty message once."""
    global _empty_message
    _empty_message = create_empty_test_all_types()


def benchmark_serialize_huge():
    """Benchmark function for creating and serializing the huge message."""
    # Create nested messages with random values
    nested_message = unittest_pb.TestAllTypes_NestedMessage(
        bb=random.randint(0, 1000000)
    )

    foreign_message = unittest_pb.ForeignMessage(
        c=random.randint(0, 1000000),
        d=random.randint(0, 1000000)
    )

    import_message = unittest_import.ImportMessage(
        d=random.randint(0, 1000000)
    )

    public_import_message = unittest_import_public.PublicImportMessage(
        e=random.randint(0, 1000000)
    )

    # Create repeated nested messages with random values
    repeated_nested_messages = [
        unittest_pb.TestAllTypes_NestedMessage(bb=random.randint(0, 1000000))
        for _ in range(50)
    ]

    repeated_foreign_messages = [
        unittest_pb.ForeignMessage(c=random.randint(0, 1000000), d=random.randint(0, 1000000))
        for _ in range(50)
    ]

    repeated_import_messages = [
        unittest_import.ImportMessage(d=random.randint(0, 1000000))
        for _ in range(50)
    ]

    # Create the huge TestAllTypes message using constructor with random values
    msg = unittest_pb.TestAllTypes(
        # Optional scalar fields - integers
        optional_int32=random.randint(-2147483648, 2147483647),
        optional_int64=random.randint(-9223372036854775808, 9223372036854775807),
        optional_uint32=random.randint(0, 4294967295),
        optional_uint64=random.randint(0, 18446744073709551615),
        optional_sint32=random.randint(-2147483648, 2147483647),
        optional_sint64=random.randint(-9223372036854775808, 9223372036854775807),
        optional_fixed32=random.randint(0, 4294967295),
        optional_fixed64=random.randint(0, 18446744073709551615),
        optional_sfixed32=random.randint(-2147483648, 2147483647),
        optional_sfixed64=random.randint(-9223372036854775808, 9223372036854775807),

        # Optional scalar fields - floats
        optional_float=random.uniform(-1e10, 1e10),
        optional_double=random.uniform(-1e100, 1e100),

        # Optional scalar fields - bool and strings
        optional_bool=random.choice([True, False]),
        optional_string="".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=460)),
        optional_bytes=bytes(random.randint(0, 255) for _ in range(1024)),

        # Optional message fields
        optional_nested_message=nested_message,
        optional_foreign_message=foreign_message,
        optional_import_message=import_message,
        optional_public_import_message=public_import_message,
        optional_lazy_message=unittest_pb.TestAllTypes_NestedMessage(bb=random.randint(0, 1000000)),
        optional_unverified_lazy_message=unittest_pb.TestAllTypes_NestedMessage(bb=random.randint(0, 1000000)),

        # Optional enum fields
        optional_nested_enum=random.choice([
            unittest_pb.TestAllTypes_NestedEnum.FOO,
            unittest_pb.TestAllTypes_NestedEnum.BAR,
            unittest_pb.TestAllTypes_NestedEnum.BAZ,
            unittest_pb.TestAllTypes_NestedEnum.NEG,
        ]),
        optional_foreign_enum=random.choice([
            unittest_pb.ForeignEnum.FOREIGN_FOO,
            unittest_pb.ForeignEnum.FOREIGN_BAR,
            unittest_pb.ForeignEnum.FOREIGN_BAZ,
        ]),
        optional_import_enum=random.choice([
            unittest_import.ImportEnum.IMPORT_FOO,
            unittest_import.ImportEnum.IMPORT_BAR,
            unittest_import.ImportEnum.IMPORT_BAZ,
        ]),

        # Optional string piece and cord
        optional_string_piece="".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=1000)),
        optional_cord="".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=1000)),

        # Repeated scalar fields - integers (large arrays)
        repeated_int32=[random.randint(-2147483648, 2147483647) for _ in range(2000)],
        repeated_int64=[random.randint(-9223372036854775808, 9223372036854775807) for _ in range(10000)],
        repeated_uint32=[random.randint(0, 4294967295) for _ in range(2000)],
        repeated_uint64=[random.randint(0, 18446744073709551615) for _ in range(2000)],
        repeated_sint32=[random.randint(-2147483648, 2147483647) for _ in range(2000)],
        repeated_sint64=[random.randint(-9223372036854775808, 9223372036854775807) for _ in range(2000)],
        repeated_fixed32=[random.randint(0, 4294967295) for _ in range(500)],
        repeated_fixed64=[random.randint(0, 18446744073709551615) for _ in range(500)],
        repeated_sfixed32=[random.randint(-2147483648, 2147483647) for _ in range(1000)],
        repeated_sfixed64=[random.randint(-9223372036854775808, 9223372036854775807) for _ in range(1000)],

        # Repeated scalar fields - floats
        repeated_float=[random.uniform(-1e10, 1e10) for _ in range(1000)],
        repeated_double=[random.uniform(-1e100, 1e100) for _ in range(1000)],

        # Repeated scalar fields - bool and strings
        repeated_bool=[random.choice([True, False]) for _ in range(100)],
        repeated_string=["".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=20)) for _ in range(100)],
        repeated_bytes=[bytes(random.randint(0, 255) for _ in range(10)) for _ in range(100)],

        # Repeated message fields
        repeated_nested_message=repeated_nested_messages,
        repeated_foreign_message=repeated_foreign_messages,
        repeated_import_message=repeated_import_messages,
        repeated_lazy_message=[
            unittest_pb.TestAllTypes_NestedMessage(bb=random.randint(0, 1000000))
            for _ in range(20)
        ],

        # Repeated enum fields
        repeated_nested_enum=[
            random.choice([
                unittest_pb.TestAllTypes_NestedEnum.FOO,
                unittest_pb.TestAllTypes_NestedEnum.BAR,
                unittest_pb.TestAllTypes_NestedEnum.BAZ,
                unittest_pb.TestAllTypes_NestedEnum.NEG,
            ])
            for _ in range(100)
        ],
        repeated_foreign_enum=[
            random.choice([
                unittest_pb.ForeignEnum.FOREIGN_FOO,
                unittest_pb.ForeignEnum.FOREIGN_BAR,
                unittest_pb.ForeignEnum.FOREIGN_BAZ,
            ])
            for _ in range(90)
        ],
        repeated_import_enum=[
            random.choice([
                unittest_import.ImportEnum.IMPORT_FOO,
                unittest_import.ImportEnum.IMPORT_BAR,
                unittest_import.ImportEnum.IMPORT_BAZ,
            ])
            for _ in range(90)
        ],

        # Repeated string piece and cord
        repeated_string_piece=["".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=30)) for _ in range(50)],
        repeated_cord=["".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=30)) for _ in range(50)],

        # Default fields (with non-default values)
        default_int32=random.randint(-2147483648, 2147483647),
        default_int64=random.randint(-9223372036854775808, 9223372036854775807),
        default_uint32=random.randint(0, 4294967295),
        default_uint64=random.randint(0, 18446744073709551615),
        default_sint32=random.randint(-2147483648, 2147483647),
        default_sint64=random.randint(-9223372036854775808, 9223372036854775807),
        default_fixed32=random.randint(0, 4294967295),
        default_fixed64=random.randint(0, 18446744073709551615),
        default_sfixed32=random.randint(-2147483648, 2147483647),
        default_sfixed64=random.randint(-9223372036854775808, 9223372036854775807),
        default_float=random.uniform(-1e10, 1e10),
        default_double=random.uniform(-1e100, 1e100),
        default_bool=random.choice([True, False]),
        default_string="".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=740)),
        default_bytes=bytes(random.randint(0, 255) for _ in range(600)),
        default_nested_enum=random.choice([
            unittest_pb.TestAllTypes_NestedEnum.FOO,
            unittest_pb.TestAllTypes_NestedEnum.BAR,
            unittest_pb.TestAllTypes_NestedEnum.BAZ,
            unittest_pb.TestAllTypes_NestedEnum.NEG,
        ]),
        default_foreign_enum=random.choice([
            unittest_pb.ForeignEnum.FOREIGN_FOO,
            unittest_pb.ForeignEnum.FOREIGN_BAR,
            unittest_pb.ForeignEnum.FOREIGN_BAZ,
        ]),
        default_import_enum=random.choice([
            unittest_import.ImportEnum.IMPORT_FOO,
            unittest_import.ImportEnum.IMPORT_BAR,
            unittest_import.ImportEnum.IMPORT_BAZ,
        ]),
        default_string_piece="".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=50)),
        default_cord="".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=50)),

        # Oneof fields (using oneof_string as an example)
        oneof_string="".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=540)),
    )

    return msg.encode()


def benchmark_serialize_nested():
    """Benchmark function for creating and serializing the nested message."""
    def create_nested(depth, max_depth=10):
        if depth >= max_depth:
            return None

        return unittest_pb.NestedTestAllTypes(
            child=create_nested(depth + 1, max_depth),
            payload=unittest_pb.TestAllTypes(
                optional_int32=random.randint(-2147483648, 2147483647),
                optional_string="".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=100)),
                repeated_int32=[random.randint(-2147483648, 2147483647) for _ in range(depth * 10)],
            ),
            repeated_child=[
                unittest_pb.NestedTestAllTypes(
                    payload=unittest_pb.TestAllTypes(
                        optional_int32=random.randint(-2147483648, 2147483647),
                    )
                )
                for _ in range(5)
            ]
        )

    msg = create_nested(0)
    return msg.encode()


def benchmark_serialize_empty():
    """Benchmark function for creating and serializing the empty message."""
    msg = unittest_pb.TestAllTypes()
    return msg.encode()


def benchmark_create_and_serialize_huge():
    """Benchmark both creation and serialization of huge message."""
    msg = create_huge_test_all_types()
    return msg.encode()


def benchmark_create_and_serialize_nested():
    """Benchmark both creation and serialization of nested message."""
    msg = create_nested_test_all_types()
    return msg.encode()


# ============================================================================
# Unit Tests
# ============================================================================

class TestProtobufMarshalling(unittest.TestCase):
    """Test cases for protobuf marshalling/serialization."""

    def test_huge_test_all_types_serialization(self):
        """
        Test serialization of a fully populated TestAllTypes message.
        This creates a huge structure with all fields filled and serializes it.
        """
        msg = create_huge_test_all_types()

        # Serialize the message
        serialized_data = msg.encode()

        # Verify that serialization produced non-empty bytes
        self.assertIsInstance(serialized_data, bytes)
        self.assertGreater(len(serialized_data), 0)

        # Print statistics about the serialized message
        print(f"\n=== Serialization Test Results ===")
        print(f"Serialized size: {len(serialized_data):,} bytes")
        print(f"Calculated protobuf size: {msg.calc_protobuf_size():,} bytes")

        # Verify that calc_protobuf_size matches actual encoded size
        self.assertEqual(len(serialized_data), msg.calc_protobuf_size())

        # Additional verification: ensure some key fields are present
        self.assertGreater(len(serialized_data), 10000,
                          "Serialized data should be substantial with all fields populated")

    def test_nested_test_all_types_serialization(self):
        """
        Test serialization of NestedTestAllTypes with deep nesting.
        Creates a deeply nested structure to test recursive serialization.
        """
        nested_msg = create_nested_test_all_types()

        # Serialize
        serialized_data = nested_msg.encode()

        # Verify
        self.assertIsInstance(serialized_data, bytes)
        self.assertGreater(len(serialized_data), 0)

        print(f"\n=== Nested Structure Serialization ===")
        print(f"Nested serialized size: {len(serialized_data):,} bytes")
        print(f"Calculated protobuf size: {nested_msg.calc_protobuf_size():,} bytes")

        self.assertEqual(len(serialized_data), nested_msg.calc_protobuf_size())

    def test_empty_test_all_types_serialization(self):
        """
        Test serialization of an empty TestAllTypes message.
        Default-initialized messages may still have some serialized size
        due to required fields or default enum values.
        """
        msg = create_empty_test_all_types()

        serialized_data = msg.encode()

        # Verify serialization works and size calculation matches
        self.assertIsInstance(serialized_data, bytes)
        self.assertEqual(len(serialized_data), msg.calc_protobuf_size())

        print(f"\n=== Empty Message Serialization ===")
        print(f"Empty message serialized size: {len(serialized_data)} bytes")
        print(f"Calculated protobuf size: {msg.calc_protobuf_size()} bytes")


# ============================================================================
# Command-line interface for benchmarking
# ============================================================================

def run_benchmarks():
    """Run timeit benchmarks and display results."""
    print("=" * 70)
    print("PROTOBUF SERIALIZATION BENCHMARKS")
    print("=" * 70)

    # Benchmark 1: Create and serialize huge message
    print("\n1. Creating and serializing huge message...")
    time_huge = timeit.timeit(
        "benchmark_serialize_huge()",
        setup="from __main__ import benchmark_serialize_huge",
        number=1000
    )
    print(f"   Time for 1000 iterations: {time_huge:.4f} seconds")
    print(f"   Average per iteration: {time_huge/1000*1000:.4f} ms")

    # Benchmark 2: Create and serialize huge message
    print("\n2. Creating and serializing huge message...")
    time_huge_create = timeit.timeit(
        "benchmark_create_and_serialize_huge()",
        setup="from __main__ import benchmark_create_and_serialize_huge",
        number=100
    )
    print(f"   Time for 100 iterations: {time_huge_create:.4f} seconds")
    print(f"   Average per iteration: {time_huge_create/100*1000:.4f} ms")

    # Benchmark 3: Create and serialize nested message
    print("\n3. Creating and serializing nested message...")
    time_nested = timeit.timeit(
        "benchmark_serialize_nested()",
        setup="from __main__ import benchmark_serialize_nested",
        number=1000
    )
    print(f"   Time for 1000 iterations: {time_nested:.4f} seconds")
    print(f"   Average per iteration: {time_nested/1000*1000:.4f} ms")

    # Benchmark 4: Create and serialize nested message
    print("\n4. Creating and serializing nested message...")
    time_nested_create = timeit.timeit(
        "benchmark_create_and_serialize_nested()",
        setup="from __main__ import benchmark_create_and_serialize_nested",
        number=1000
    )
    print(f"   Time for 1000 iterations: {time_nested_create:.4f} seconds")
    print(f"   Average per iteration: {time_nested_create/1000*1000:.4f} ms")

    # Benchmark 5: Create and serialize empty message
    print("\n5. Creating and serializing empty message...")
    time_empty = timeit.timeit(
        "benchmark_serialize_empty()",
        setup="from __main__ import benchmark_serialize_empty",
        number=10000
    )
    print(f"   Time for 10000 iterations: {time_empty:.4f} seconds")
    print(f"   Average per iteration: {time_empty/10000*1000:.4f} ms")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--benchmark':
        run_benchmarks()
    else:
        unittest.main(verbosity=2)
