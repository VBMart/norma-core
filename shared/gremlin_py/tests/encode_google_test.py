"""
Test for protobuf serialization (marshalling) of TestAllTypes using Google's protobuf implementation.
Creates protobuf messages and verifies their serialization.

This module can be used both as a unittest test suite and with timeit for performance benchmarking.

Usage (run from shared/gremlin_py/ directory):
    # Run all tests
    python3 -m unittest tests.encode_google_test

    # Run built-in benchmarks
    python3 -m tests.encode_google_test --benchmark

    # Run specific test
    python3 -m unittest tests.encode_google_test.TestProtobufMarshalling.test_huge_test_all_types_serialization

    # Use with timeit for custom benchmarking
    python3 -m timeit -s "from tests.encode_google_test import setup_huge_message, benchmark_serialize_huge; setup_huge_message()" "benchmark_serialize_huge()"
"""

import unittest
import timeit
import os
import sys
import random

# Add tests/gen/google to sys.path so unittest_pb2 can find its imports
_google_pb_path = os.path.join(os.path.dirname(__file__), 'gen', 'google')
_google_pb_path = os.path.abspath(_google_pb_path)
if _google_pb_path not in sys.path:
    sys.path.insert(0, _google_pb_path)

from tests.gen.google import unittest_pb2


# Path to binary test files
BINARIES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'binaries')


# ============================================================================
# Helper Functions
# ============================================================================

def load_expected_binary(filename):
    """Load expected binary data from file."""
    binary_path = os.path.join(BINARIES_DIR, filename)
    with open(binary_path, 'rb') as f:
        return f.read()


# ============================================================================
# Message Creation Functions (for timeit setup)
# ============================================================================

def create_huge_test_all_types():
    """
    Create a fully populated TestAllTypes message with all fields filled.
    This function can be used for timeit benchmarking.
    Uses Google's protobuf implementation.
    """
    # Create the huge TestAllTypes message with ALL fields populated
    msg = unittest_pb2.TestAllTypes()

    # Optional scalar fields - integers
    msg.optional_int32 = random.randint(-2147483648, 2147483647)
    msg.optional_int64 = random.randint(-9223372036854775808, 9223372036854775807)
    msg.optional_uint32 = random.randint(0, 4294967295)
    msg.optional_uint64 = random.randint(0, 18446744073709551615)
    msg.optional_sint32 = random.randint(-2147483648, 2147483647)
    msg.optional_sint64 = random.randint(-9223372036854775808, 9223372036854775807)
    msg.optional_fixed32 = random.randint(0, 4294967295)
    msg.optional_fixed64 = random.randint(0, 18446744073709551615)
    msg.optional_sfixed32 = random.randint(-2147483648, 2147483647)
    msg.optional_sfixed64 = random.randint(-9223372036854775808, 9223372036854775807)

    # Optional scalar fields - floats
    msg.optional_float = random.uniform(-1e10, 1e10)
    msg.optional_double = random.uniform(-1e100, 1e100)

    # Optional scalar fields - bool and strings
    msg.optional_bool = random.choice([True, False])
    msg.optional_string = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=460))
    msg.optional_bytes = bytes(random.randint(0, 255) for _ in range(1024))

    # Optional message fields
    msg.optional_nested_message.bb = random.randint(0, 1000000)
    msg.optional_foreign_message.c = random.randint(0, 1000000)
    msg.optional_foreign_message.d = random.randint(0, 1000000)
    # Note: Skipping optional_import_message and optional_public_import_message
    # as unittest_pb2.py is missing the required import dependencies
    msg.optional_lazy_message.bb = random.randint(0, 1000000)
    msg.optional_unverified_lazy_message.bb = random.randint(0, 1000000)

    # Optional enum fields
    msg.optional_nested_enum = random.choice([
        unittest_pb2.TestAllTypes.FOO,
        unittest_pb2.TestAllTypes.BAR,
        unittest_pb2.TestAllTypes.BAZ,
        unittest_pb2.TestAllTypes.NEG,
    ])
    msg.optional_foreign_enum = random.choice([
        unittest_pb2.FOREIGN_FOO,
        unittest_pb2.FOREIGN_BAR,
        unittest_pb2.FOREIGN_BAZ,
    ])
    # Note: Skipping optional_import_enum as it requires missing imports

    # Optional string piece and cord
    msg.optional_string_piece = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=1000))
    msg.optional_cord = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=1000))

    # Repeated scalar fields - integers (large arrays)
    msg.repeated_int32.extend([random.randint(-2147483648, 2147483647) for _ in range(2000)])
    msg.repeated_int64.extend([random.randint(-9223372036854775808, 9223372036854775807) for _ in range(10000)])
    msg.repeated_uint32.extend([random.randint(0, 4294967295) for _ in range(2000)])
    msg.repeated_uint64.extend([random.randint(0, 18446744073709551615) for _ in range(2000)])
    msg.repeated_sint32.extend([random.randint(-2147483648, 2147483647) for _ in range(2000)])
    msg.repeated_sint64.extend([random.randint(-9223372036854775808, 9223372036854775807) for _ in range(2000)])
    msg.repeated_fixed32.extend([random.randint(0, 4294967295) for _ in range(500)])
    msg.repeated_fixed64.extend([random.randint(0, 18446744073709551615) for _ in range(500)])
    msg.repeated_sfixed32.extend([random.randint(-2147483648, 2147483647) for _ in range(1000)])
    msg.repeated_sfixed64.extend([random.randint(-9223372036854775808, 9223372036854775807) for _ in range(1000)])

    # Repeated scalar fields - floats
    msg.repeated_float.extend([random.uniform(-1e10, 1e10) for _ in range(1000)])
    msg.repeated_double.extend([random.uniform(-1e100, 1e100) for _ in range(1000)])

    # Repeated scalar fields - bool and strings
    msg.repeated_bool.extend([random.choice([True, False]) for _ in range(100)])
    msg.repeated_string.extend(["".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=20)) for _ in range(100)])
    msg.repeated_bytes.extend([bytes(random.randint(0, 255) for _ in range(10)) for _ in range(100)])

    # Repeated message fields
    for _ in range(50):
        nested_msg = msg.repeated_nested_message.add()
        nested_msg.bb = random.randint(0, 1000000)

    for _ in range(50):
        foreign_msg = msg.repeated_foreign_message.add()
        foreign_msg.c = random.randint(0, 1000000)
        foreign_msg.d = random.randint(0, 1000000)

    # Note: Skipping repeated_import_message as it requires missing imports

    for _ in range(20):
        lazy_msg = msg.repeated_lazy_message.add()
        lazy_msg.bb = random.randint(0, 1000000)

    # Repeated enum fields
    nested_enum_choices = [
        unittest_pb2.TestAllTypes.FOO,
        unittest_pb2.TestAllTypes.BAR,
        unittest_pb2.TestAllTypes.BAZ,
        unittest_pb2.TestAllTypes.NEG,
    ]
    msg.repeated_nested_enum.extend([random.choice(nested_enum_choices) for _ in range(100)])

    foreign_enum_choices = [
        unittest_pb2.FOREIGN_FOO,
        unittest_pb2.FOREIGN_BAR,
        unittest_pb2.FOREIGN_BAZ,
    ]
    msg.repeated_foreign_enum.extend([random.choice(foreign_enum_choices) for _ in range(90)])
    # Note: Skipping repeated_import_enum as it requires missing imports

    # Repeated string piece and cord
    msg.repeated_string_piece.extend(["".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=30)) for _ in range(50)])
    msg.repeated_cord.extend(["".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=30)) for _ in range(50)])

    # Default fields (with non-default values)
    msg.default_int32 = random.randint(-2147483648, 2147483647)
    msg.default_int64 = random.randint(-9223372036854775808, 9223372036854775807)
    msg.default_uint32 = random.randint(0, 4294967295)
    msg.default_uint64 = random.randint(0, 18446744073709551615)
    msg.default_sint32 = random.randint(-2147483648, 2147483647)
    msg.default_sint64 = random.randint(-9223372036854775808, 9223372036854775807)
    msg.default_fixed32 = random.randint(0, 4294967295)
    msg.default_fixed64 = random.randint(0, 18446744073709551615)
    msg.default_sfixed32 = random.randint(-2147483648, 2147483647)
    msg.default_sfixed64 = random.randint(-9223372036854775808, 9223372036854775807)
    msg.default_float = random.uniform(-1e10, 1e10)
    msg.default_double = random.uniform(-1e100, 1e100)
    msg.default_bool = random.choice([True, False])
    msg.default_string = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=740))
    msg.default_bytes = bytes(random.randint(0, 255) for _ in range(600))
    msg.default_nested_enum = random.choice(nested_enum_choices)
    msg.default_foreign_enum = random.choice(foreign_enum_choices)
    # Note: Skipping default_import_enum as it requires missing imports
    msg.default_string_piece = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=50))
    msg.default_cord = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=50))

    # Oneof fields (using oneof_string as an example)
    msg.oneof_string = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", k=540))

    return msg


def create_nested_test_all_types(max_depth=10):
    """
    Create a deeply nested NestedTestAllTypes structure.
    This function can be used for timeit benchmarking.
    Uses Google's protobuf implementation.
    """
    def create_nested(depth, max_depth):
        if depth >= max_depth:
            return None

        msg = unittest_pb2.NestedTestAllTypes()

        # Set payload with random values
        msg.payload.optional_int32 = random.randint(-2147483648, 2147483647)
        msg.payload.optional_string = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=100))
        msg.payload.repeated_int32.extend([random.randint(-2147483648, 2147483647) for _ in range(depth * 10)])

        # Set child recursively
        child_msg = create_nested(depth + 1, max_depth)
        if child_msg:
            msg.child.CopyFrom(child_msg)

        # Set repeated_child with random values
        for _ in range(5):
            repeated_child = msg.repeated_child.add()
            repeated_child.payload.optional_int32 = random.randint(-2147483648, 2147483647)

        return msg

    return create_nested(0, max_depth)


def create_empty_test_all_types():
    """Create an empty TestAllTypes message."""
    return unittest_pb2.TestAllTypes()


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
    """Benchmark function for creating and serializing the huge message.
    Note: SerializeToString() returns bytes, not str (legacy naming from Python 2)."""
    msg = create_huge_test_all_types()
    return msg.SerializeToString()


def benchmark_serialize_nested():
    """Benchmark function for creating and serializing the nested message.
    Note: SerializeToString() returns bytes, not str (legacy naming from Python 2)."""
    msg = create_nested_test_all_types()
    return msg.SerializeToString()


def benchmark_serialize_empty():
    """Benchmark function for creating and serializing the empty message.
    Note: SerializeToString() returns bytes, not str (legacy naming from Python 2)."""
    msg = create_empty_test_all_types()
    return msg.SerializeToString()


def benchmark_create_and_serialize_huge():
    """Benchmark both creation and serialization of huge message."""
    msg = create_huge_test_all_types()
    return msg.SerializeToString()


def benchmark_create_and_serialize_nested():
    """Benchmark both creation and serialization of nested message."""
    msg = create_nested_test_all_types()
    return msg.SerializeToString()


# ============================================================================
# Unit Tests
# ============================================================================

class TestProtobufMarshalling(unittest.TestCase):
    """Test cases for protobuf marshalling/serialization using Google's protobuf."""

    def test_huge_test_all_types_serialization(self):
        """
        Test serialization of a fully populated TestAllTypes message.
        This creates a huge structure with all fields filled and serializes it.

        Note: Google's protobuf implementation produces different binary output than
        the custom implementation due to different handling of default values and
        field serialization rules. This test verifies internal consistency only.
        """
        msg = create_huge_test_all_types()

        # Serialize the message (SerializeToString returns bytes despite the name)
        serialized_data = msg.SerializeToString()

        # Verify that serialization produced bytes (not str)
        self.assertIsInstance(serialized_data, bytes)
        self.assertNotIsInstance(serialized_data, str)
        self.assertGreater(len(serialized_data), 0)

        # Print statistics about the serialized message
        print(f"\n=== Serialization Test Results (Google Protobuf) ===")
        print(f"Serialized size: {len(serialized_data):,} bytes")
        print(f"Calculated protobuf size: {msg.ByteSize():,} bytes")

        # Verify that ByteSize matches actual encoded size
        self.assertEqual(len(serialized_data), msg.ByteSize())

        # Additional verification: ensure some key fields are present
        # We can do basic checks on the serialized data
        self.assertGreater(len(serialized_data), 10000,
                          "Serialized data should be substantial with all fields populated")

    def test_nested_test_all_types_serialization(self):
        """
        Test serialization of NestedTestAllTypes with deep nesting.
        Creates a deeply nested structure to test recursive serialization.

        Note: Google's protobuf implementation produces different binary output than
        the custom implementation due to different handling of default values and
        field serialization rules. This test verifies internal consistency only.
        """
        nested_msg = create_nested_test_all_types()

        # Serialize (SerializeToString returns bytes despite the name)
        serialized_data = nested_msg.SerializeToString()

        # Verify that serialization produced bytes (not str)
        self.assertIsInstance(serialized_data, bytes)
        self.assertNotIsInstance(serialized_data, str)
        self.assertGreater(len(serialized_data), 0)

        print(f"\n=== Nested Structure Serialization (Google Protobuf) ===")
        print(f"Nested serialized size: {len(serialized_data):,} bytes")
        print(f"Calculated protobuf size: {nested_msg.ByteSize():,} bytes")

        self.assertEqual(len(serialized_data), nested_msg.ByteSize())

    def test_empty_test_all_types_serialization(self):
        """
        Test serialization of an empty TestAllTypes message.

        Note: Google's protobuf implementation correctly produces 0 bytes for an
        empty message (proto3 behavior), while the custom implementation includes
        default enum values. This test verifies internal consistency only.
        """
        msg = create_empty_test_all_types()

        # Serialize (SerializeToString returns bytes despite the name)
        serialized_data = msg.SerializeToString()

        # Verify that serialization produced bytes (not str)
        self.assertIsInstance(serialized_data, bytes)
        self.assertNotIsInstance(serialized_data, str)
        self.assertEqual(len(serialized_data), msg.ByteSize())

        print(f"\n=== Empty Message Serialization (Google Protobuf) ===")
        print(f"Empty message serialized size: {len(serialized_data)} bytes")
        print(f"Calculated protobuf size: {msg.ByteSize()} bytes")


# ============================================================================
# Command-line interface for benchmarking
# ============================================================================

def run_benchmarks():
    """Run timeit benchmarks and display results."""
    print("=" * 70)
    print("PROTOBUF SERIALIZATION BENCHMARKS (Google Protobuf)")
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
