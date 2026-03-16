"""
Example: Control motors with simple input

This demonstrates how EASY it is to control motors with station_py!

Controls servo with ID = 1 on ALL buses.

Just enter a position from 0.0 to 1.0:
  0.0 - Minimum position (range_min)
  1.0 - Maximum position (range_max)
  0.5 - Middle position
  q   - Quit

The example subscribes to motor state and maps normalized positions
to each motor's calibrated range. Real-time control in just a few lines of code!
"""

import asyncio
import sys
import logging
import struct
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from station_py import new_station_client, send_commands, StreamEntry

# Import protobuf messages
from target.gen_python.protobuf.station import commands, drivers
from target.gen_python.protobuf.drivers.st3215 import st3215

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Motor state
PRESENT_POSITION_ADDR = 0x38  # 2 bytes
MAX_ANGLE_STEP = 4095
SIGN_BIT_MASK = 0x8000

# Global state - tracks all buses
buses_info = {}  # {bus_serial: {'motor_id': int, 'position': int, 'range_min': int, 'range_max': int}}

# Target motor ID to control
TARGET_MOTOR_ID = 1


def normal_position(position: int) -> int:
    """Normalize position value (handle sign bit)."""
    if position & SIGN_BIT_MASK != 0:
        magnitude = position & MAX_ANGLE_STEP
        return (MAX_ANGLE_STEP + 1 - magnitude) & MAX_ANGLE_STEP
    else:
        return position & MAX_ANGLE_STEP


def parse_position(state_bytes: memoryview) -> int:
    """Extract position from motor state bytes."""
    state = bytes(state_bytes)
    if len(state) >= PRESENT_POSITION_ADDR + 2:
        raw_pos = struct.unpack('<H', state[PRESENT_POSITION_ADDR:PRESENT_POSITION_ADDR + 2])[0]
        return normal_position(raw_pos)
    return 0


def move_motors(client, position: int):
    """Move all first servos on all buses to target position."""
    global buses_info

    # Build commands for all buses
    command_list = []
    skipped = []

    for bus_serial, info in buses_info.items():
        range_min = info.get('range_min', 0)
        range_max = info.get('range_max', 0)

        # Check if range is defined (both min and max should be non-zero and different)
        if range_min == 0 and range_max == 0:
            skipped.append(f"Bus {bus_serial}: Range not calibrated")
            continue

        if range_min >= range_max:
            skipped.append(f"Bus {bus_serial}: Invalid range [{range_min}, {range_max}]")
            continue

        # Clamp position to motor's calibrated range
        clamped_position = max(range_min, min(range_max, position))

        if clamped_position != position:
            logger.warning(f"Bus {bus_serial}: Position {position} clamped to range [{range_min}, {range_max}] -> {clamped_position}")

        # Create ST3215 command
        # Convert bus_serial to string (the protobuf expects string even though type hint says bytes)
        bus_serial_str = bus_serial.decode('utf-8') if isinstance(bus_serial, bytes) else bus_serial

        st3215_cmd = st3215.Command(
            target_bus_serial=bus_serial_str,
            write=st3215.ST3215WriteCommand(
                motor_id=info['motor_id'],
                address=0x2A,  # Target position register
                value=clamped_position.to_bytes(2, byteorder='little')
            )
        )

        # Wrap in DriverCommand
        cmd = commands.DriverCommand(
            type=drivers.StationCommandType.STC_ST3215_COMMAND,
            body=st3215_cmd.encode()
        )
        command_list.append(cmd)

    # Print warnings for skipped motors
    for warning in skipped:
        logger.warning(f"⚠ Skipping command - {warning}")

    if command_list:
        send_commands(client, command_list)
        logger.info(f"→ Moving {len(command_list)} servo(s) to position {position}")
    elif skipped:
        logger.error("❌ No commands sent - all motors need calibration!")


async def state_subscriber(client):
    """Subscribe to motor state updates and track current position for all buses."""
    global buses_info

    entries_queue = asyncio.Queue()
    error_queue = client.follow("st3215/inference", entries_queue)

    logger.info("Subscribed to st3215/inference")

    while True:
        # Check for errors
        if not error_queue.empty():
            error = await error_queue.get()
            logger.error(f"Subscription error: {error}")
            break

        # Get next entry
        try:
            entry: StreamEntry = await asyncio.wait_for(entries_queue.get(), timeout=1.0)

            if entry is None:
                break

            # Parse inference state
            data_bytes = bytes(entry.Data)
            inference_state = st3215.InferenceStateReader(memoryview(data_bytes))

            buses = inference_state.get_buses()
            if buses:
                for bus_state in buses:
                    bus_info = bus_state.get_bus()
                    if not bus_info:
                        continue

                    bus_serial = bus_info.get_serial_number()
                    motors = bus_state.get_motors()

                    if motors:
                        # Find motor with target ID
                        target_motor = None
                        for motor_state in motors:
                            if motor_state.get_id() == TARGET_MOTOR_ID:
                                target_motor = motor_state
                                break

                        if target_motor:
                            motor_id = target_motor.get_id()
                            range_min = target_motor.get_range_min()
                            range_max = target_motor.get_range_max()

                            # Initialize bus info if first time seeing it
                            if bus_serial not in buses_info:
                                buses_info[bus_serial] = {
                                    'motor_id': motor_id,
                                    'position': 0,
                                    'range_min': range_min,
                                    'range_max': range_max
                                }
                                if range_min > 0 or range_max > 0:
                                    logger.info(f"Found bus {bus_serial}, servo ID {motor_id}, range=[{range_min}, {range_max}]")
                                else:
                                    logger.warning(f"Found bus {bus_serial}, servo ID {motor_id}, ⚠ NOT CALIBRATED")

                            # Update current position and ranges
                            buses_info[bus_serial]['range_min'] = range_min
                            buses_info[bus_serial]['range_max'] = range_max

                            state_bytes = target_motor.get_state()
                            if state_bytes:
                                buses_info[bus_serial]['position'] = parse_position(state_bytes)

        except asyncio.TimeoutError:
            continue


async def input_handler(client):
    """Handle user input for motor control."""
    global buses_info

    logger.info("")
    logger.info("=" * 60)
    logger.info("  MOTOR CONTROL DEMO")
    logger.info("=" * 60)
    logger.info("")
    logger.info("  Enter position from 0.0 to 1.0 (q to quit)")
    logger.info("  Position will be mapped to each motor's calibrated range")
    logger.info("")
    logger.info("=" * 60)
    logger.info("")

    # Wait for at least one bus
    while len(buses_info) == 0:
        await asyncio.sleep(0.1)

    logger.info(f"Ready! Controlling {len(buses_info)} bus(es)")

    # Show motor ranges
    for bus_serial, info in buses_info.items():
        logger.info(f"  Bus {bus_serial}: range=[{info['range_min']}, {info['range_max']}]")

    logger.info("")

    try:
        while True:
            # Use run_in_executor to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, input, "Position (0.0-1.0): ")

            user_input = user_input.strip().lower()

            if user_input == 'q':
                logger.info("Exiting...")
                break

            try:
                position_normalized = float(user_input)

                if position_normalized < 0.0 or position_normalized > 1.0:
                    logger.warning("Position must be between 0.0 and 1.0")
                    continue

                # Map normalized position to each motor's range
                for bus_serial, info in buses_info.items():
                    range_min = info.get('range_min', 0)
                    range_max = info.get('range_max', 0)

                    if range_min > 0 or range_max > 0:
                        # Map 0-1 to range_min - range_max
                        target_pos = int(range_min + (range_max - range_min) * position_normalized)
                        move_motors(client, target_pos)
                        break  # Only need to calculate once since move_motors handles all buses

            except ValueError:
                logger.warning("Invalid input. Please enter a number between 0.0 and 1.0, or 'q' to quit")
                continue

    except KeyboardInterrupt:
        logger.info("\nExiting...")


async def main_async():
    """Main async function."""

    # Connect to station
    logger.info("Connecting to station...")
    client = new_station_client("localhost", logger)
    logger.info("Connected!")

    # Run state subscriber and input handler concurrently
    await asyncio.gather(
        state_subscriber(client),
        input_handler(client)
    )


def main():
    """Entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
