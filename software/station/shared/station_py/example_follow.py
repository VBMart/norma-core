"""
Example: Following the st3215/inference queue

This demonstrates how to use the follow() method to continuously
stream entries from a queue as they arrive, and parse motor state data.
"""

import asyncio
import logging
import sys
import struct
import time
from pathlib import Path

# Add paths for imports
# - Parent directory for station_py module
# - norma_core root for target/gen_python protobuf imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from station_py import new_station_client, StreamEntry
from target.gen_python.protobuf.drivers.st3215 import st3215 as st3215_pb2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ST3215 Register addresses (from protocol/memory.rs)
PRESENT_POSITION_ADDR = 0x38  # 2 bytes
PRESENT_VOLTAGE_ADDR = 0x3E   # 1 byte
PRESENT_TEMPERATURE_ADDR = 0x3F  # 1 byte
PRESENT_CURRENT_ADDR = 0x45   # 2 bytes

MAX_ANGLE_STEP = 4095
SIGN_BIT_MASK = 0x8000


def normal_position(position: int) -> int:
    """Normalize position value (handle sign bit)."""
    if position & SIGN_BIT_MASK != 0:
        magnitude = position & MAX_ANGLE_STEP
        return (MAX_ANGLE_STEP + 1 - magnitude) & MAX_ANGLE_STEP
    else:
        return position & MAX_ANGLE_STEP


def parse_motor_state(state_bytes: memoryview) -> dict:
    """
    Parse motor state bytes to extract position, current, temperature, and voltage.

    Args:
        state_bytes: Raw motor state data

    Returns:
        Dictionary with parsed motor values
    """
    state = bytes(state_bytes)

    result = {
        'position': 0,
        'current': 0,
        'temperature': 0,
        'voltage': 0,
    }

    # Position (2 bytes at 0x38)
    if len(state) >= PRESENT_POSITION_ADDR + 2:
        raw_pos = struct.unpack('<H', state[PRESENT_POSITION_ADDR:PRESENT_POSITION_ADDR + 2])[0]
        result['position'] = normal_position(raw_pos)

    # Current (2 bytes at 0x45) - in milliamps
    if len(state) >= PRESENT_CURRENT_ADDR + 2:
        result['current'] = struct.unpack('<H', state[PRESENT_CURRENT_ADDR:PRESENT_CURRENT_ADDR + 2])[0]

    # Temperature (1 byte at 0x3F) - in degrees Celsius
    if len(state) >= PRESENT_TEMPERATURE_ADDR + 1:
        result['temperature'] = state[PRESENT_TEMPERATURE_ADDR]

    # Voltage (1 byte at 0x3E) - in 0.1V units
    if len(state) >= PRESENT_VOLTAGE_ADDR + 1:
        result['voltage'] = state[PRESENT_VOLTAGE_ADDR] / 10.0  # Convert to volts

    return result


async def process_inference_entries():
    """Process entries from the st3215/inference queue."""

    # Create a queue to receive entries
    entries_queue = asyncio.Queue()

    # Check for errors periodically
    error_queue = None

    try:
        # Create client (will auto-connect to localhost:8888)
        client = new_station_client("localhost", logger)

        # Start following the queue
        error_queue = client.follow("st3215/inference", entries_queue)
        logger.info("Started following st3215/inference queue")

        # Process entries as they arrive
        while True:
            # Check for errors
            if not error_queue.empty():
                error = await error_queue.get()
                logger.error(f"Follow error: {error}")
                break

            # Get next entry (with timeout to check errors periodically)
            try:
                entry: StreamEntry = await asyncio.wait_for(
                    entries_queue.get(),
                    timeout=1.0
                )

                if entry is None:
                    logger.info("Stream ended")
                    break

                # Parse the InferenceState protobuf
                try:
                    data_bytes = bytes(entry.Data)
                    inference_state = st3215_pb2.InferenceStateReader(memoryview(data_bytes))
                    
                    # Print each bus and its motors
                    buses = inference_state.get_buses()
                    if buses:
                        print("ST3215 Motor State Monitor")
                        print("=" * 80)

                        for bus_state in buses:
                            bus_info = bus_state.get_bus()
                            if bus_info:
                                # Calculate latency (current time - system_stamp)
                                system_stamp_ns = bus_state.get_system_stamp_ns()
                                current_time_ns = time.time_ns()
                                latency_ns = current_time_ns - system_stamp_ns
                                latency_ms = latency_ns / 1_000_000  # Convert to milliseconds

                                print(f"\nBus: {bus_info.get_port_name()} (SN: {bus_info.get_serial_number()})")
                                print(f"Latency: {latency_ms:.2f}ms")
                                print("-" * 80)

                                motors = bus_state.get_motors()
                                if motors:
                                    for motor_state in motors:
                                        motor_id = motor_state.get_id()
                                        state_bytes = motor_state.get_state()

                                        if state_bytes:
                                            motor_data = parse_motor_state(state_bytes)

                                            print(f"  Motor {motor_id:2d}: "
                                                  f"pos={motor_data['position']:4d}, "
                                                  f"current={motor_data['current']:4d}mA, "
                                                  f"temp={motor_data['temperature']:3d}°C, "
                                                  f"voltage={motor_data['voltage']:4.1f}V")
                                        else:
                                            print(f"  Motor {motor_id:2d}: (no state data)")
                                else:
                                    print("  No motors detected")
                        print("=" * 80)

                except Exception as parse_error:
                    logger.error(f"Failed to parse inference state: {parse_error}", exc_info=True)

            except asyncio.TimeoutError:
                # No entry yet, loop will check for errors and continue
                continue

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


def main():
    """Run the example."""
    asyncio.run(process_inference_entries())


if __name__ == "__main__":
    main()
