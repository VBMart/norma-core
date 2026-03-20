"""ST3215 servo register map and state-parsing helpers.

Register addresses sourced from:
  /software/drivers/st3215/src/protocol/memory.rs
  /software/drivers/st3215/src/protocol/units.rs
"""

import struct
import asyncio
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from software.station.shared.station_py import send_commands
from target.gen_python.protobuf.station import commands, drivers
from target.gen_python.protobuf.drivers.st3215 import st3215

# =============================================================================
# Position constants
# =============================================================================

MAX_ANGLE_STEP = 4095
SIGN_BIT_MASK = 0x8000
FULL_RANGE = 4096

# =============================================================================
# Calibration constants
# =============================================================================

MOTOR_STARTUP_STEPS = 5
VELOCITY_THRESHOLD = 10
SKIP_INITIAL_SAMPLES = 3
SAFE_OFFSET = 200
CALIBRATION_STEP = 300


# =============================================================================
# EEPROM registers (non-volatile)
# =============================================================================

EEPROM_MODEL_NUMBER = 0x00          # 2 bytes
EEPROM_FIRMWARE_VERSION = 0x02      # 1 byte
EEPROM_ID = 0x05                    # 1 byte
EEPROM_BAUD_RATE = 0x06             # 1 byte
EEPROM_RETURN_DELAY = 0x07          # 1 byte
EEPROM_RESPONSE_STATUS = 0x08       # 1 byte
EEPROM_MIN_ANGLE_LIMIT = 0x09       # 2 bytes
EEPROM_MAX_ANGLE_LIMIT = 0x0B       # 2 bytes
EEPROM_MAX_TEMPERATURE = 0x0D       # 1 byte
EEPROM_MAX_VOLTAGE = 0x0E           # 1 byte
EEPROM_MIN_VOLTAGE = 0x0F           # 1 byte
EEPROM_MAX_TORQUE = 0x10            # 2 bytes
EEPROM_UNLOAD_CONDITION = 0x12      # 1 byte
EEPROM_LED_ALARM = 0x13             # 1 byte
EEPROM_P_COEF = 0x15                # 1 byte
EEPROM_D_COEF = 0x16                # 1 byte
EEPROM_I_COEF = 0x17                # 1 byte
EEPROM_MIN_STARTUP_FORCE = 0x18     # 2 bytes
EEPROM_CW_DEAD_ZONE = 0x1A          # 1 byte
EEPROM_CCW_DEAD_ZONE = 0x1B         # 1 byte
EEPROM_PROTECTION_CURRENT = 0x1C    # 2 bytes
EEPROM_ANGULAR_RESOLUTION = 0x1E    # 1 byte
EEPROM_OFFSET = 0x1F                # 2 bytes (signed)
EEPROM_MODE = 0x21                  # 1 byte
EEPROM_PROTECTION_TORQUE = 0x22     # 1 byte
EEPROM_PROTECTION_TIME = 0x23       # 1 byte
EEPROM_OVERLOAD_TORQUE = 0x24       # 1 byte
EEPROM_SPEED_CLOSED_LOOP_P = 0x25   # 1 byte
EEPROM_OVERCURRENT_PROT_TIME = 0x26 # 1 byte
EEPROM_VELOCITY_CLOSED_LOOP_I = 0x27  # 1 byte


# =============================================================================
# RAM registers (volatile, runtime)
# =============================================================================

RAM_TORQUE_ENABLE = 0x28        # 1 byte
RAM_ACC = 0x29                  # 1 byte
RAM_GOAL_POSITION = 0x2A        # 2 bytes
RAM_GOAL_TIME = 0x2C            # 2 bytes
RAM_GOAL_SPEED = 0x2E           # 2 bytes
RAM_TORQUE_LIMIT = 0x30         # 2 bytes
RAM_LOCK = 0x37                 # 1 byte (0=unlock EEPROM, 1=lock)
RAM_PRESENT_POSITION = 0x38     # 2 bytes (read-only)
RAM_PRESENT_SPEED = 0x3A        # 2 bytes (read-only)
RAM_PRESENT_LOAD = 0x3C         # 2 bytes (read-only)
RAM_PRESENT_VOLTAGE = 0x3E      # 1 byte (read-only)
RAM_PRESENT_TEMPERATURE = 0x3F  # 1 byte (read-only)
RAM_STATUS = 0x40               # 1 byte (read-only)
RAM_MOVING = 0x42               # 1 byte (read-only)
RAM_PRESENT_CURRENT = 0x45      # 2 bytes (read-only)


# =============================================================================
# State-parsing helpers
# =============================================================================

def normal_position(raw: int) -> int:
    """Normalize position value (handle sign bit for 12-bit encoder)."""
    if raw & SIGN_BIT_MASK != 0:
        magnitude = raw & MAX_ANGLE_STEP
        return (MAX_ANGLE_STEP + 1 - magnitude) & MAX_ANGLE_STEP
    return raw & MAX_ANGLE_STEP


def get_position(state: bytes | memoryview) -> int:
    """Extract present position from motor state bytes."""
    if len(state) < RAM_PRESENT_POSITION + 2:
        return 0
    raw = struct.unpack_from('<H', state, RAM_PRESENT_POSITION)[0]
    return normal_position(raw)


def get_velocity(state: bytes | memoryview) -> int:
    """Extract present speed from motor state bytes."""
    if len(state) < RAM_PRESENT_SPEED + 2:
        return 0
    return struct.unpack_from('<H', state, RAM_PRESENT_SPEED)[0]


def get_current(state: bytes | memoryview) -> int:
    """Extract present current (mA) from motor state bytes."""
    if len(state) < RAM_PRESENT_CURRENT + 2:
        return 0
    return struct.unpack_from('<H', state, RAM_PRESENT_CURRENT)[0]


def get_offset(state: bytes | memoryview) -> int:
    """Extract position offset (signed) from motor state bytes."""
    if len(state) < EEPROM_OFFSET + 2:
        return 0
    return struct.unpack_from('<h', state, EEPROM_OFFSET)[0]


# =============================================================================
# ST3215 Driver
# =============================================================================

COMMAND_TIMEOUT_S = 5.0
VERIFY_TIMEOUT_S = 5.0

class St3215Driver:
    """ST3215 servo driver with state and command tracking (universal for all buses)."""

    def __init__(self, client):
        self.client = client
        self.command_counter = 0

        # Subscribe to st3215/inference stream
        self.inference_queue = asyncio.Queue()
        self.error_queue = client.follow("st3215/inference", self.inference_queue)
        self.latest_state = None

    def next_command_id(self) -> bytes:
        """Generate next command ID as little-endian u64 bytes."""
        self.command_counter += 1
        return self.command_counter.to_bytes(8, byteorder='little')

    async def read_next_state(self):
        """Read next inference entry from stream and cache it."""
        if not self.error_queue.empty():
            error = self.error_queue.get_nowait()
            raise RuntimeError(f"Inference stream error: {error}")

        entry = await asyncio.wait_for(
            self.inference_queue.get(), timeout=COMMAND_TIMEOUT_S,
        )
        if entry is None:
            raise RuntimeError("Inference stream closed")
        self.latest_state = st3215.InferenceStateReader(entry.Data)
        return self.latest_state

    def _find_motor(self, state, bus_serial: str, motor_id: int):
        """Find motor reader object in parsed inference state."""
        for bus in (state.get_buses() or []):
            bus_info = bus.get_bus()
            if not bus_info or bus_info.get_serial_number() != bus_serial:
                continue
            for motor in (bus.get_motors() or []):
                if motor.get_id() == motor_id:
                    return motor
        return None

    def get_motor_state(self, bus_serial: str, motor_id: int) -> memoryview:
        """Return raw state bytes for motor from latest cached state."""
        if self.latest_state is None:
            raise RuntimeError("No state available")
        motor = self._find_motor(self.latest_state, bus_serial, motor_id)
        if motor is None:
            raise RuntimeError(f"Motor {motor_id} not found")
        return motor.get_state()

    def get_encoder_position(self, bus_serial: str, motor_id: int) -> int:
        """Compute encoder position = (displayed + offset) % 4096 from cache."""
        state_bytes = self.get_motor_state(bus_serial, motor_id)
        position = get_position(state_bytes)
        offset = get_offset(state_bytes)
        return (position + offset + FULL_RANGE) % FULL_RANGE

    async def send_st3215_command(self, cmd) -> bytes:
        """Wrap st3215.Command in DriverCommand and send to station."""
        command_id = self.next_command_id()

        driver_cmd = commands.DriverCommand(
            command_id=command_id,
            type=drivers.StationCommandType.STC_ST3215_COMMAND,
            body=cmd.encode(),
        )
        await send_commands(self.client, [driver_cmd])
        return command_id

    async def wait_for_command_result(self, bus_serial: str, motor_id: int, command_id: bytes):
        """Wait until command appears in specified motor's last_command with success status."""
        deadline = time.monotonic() + COMMAND_TIMEOUT_S

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Command timeout: motor {motor_id}, {command_id.hex()}")

            try:
                state = await asyncio.wait_for(
                    self.read_next_state(), timeout=remaining,
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"Command timeout: motor {motor_id}, {command_id.hex()}") from None

            motor = self._find_motor(state, bus_serial, motor_id)
            if motor is None:
                continue

            last_command = motor.get_last_command()
            if last_command is None:
                continue

            command = last_command.get_command()
            if command is None:
                continue

            if bytes(command.get_command_id()) == command_id:
                result = last_command.get_result()
                if result == st3215.CommandResult.CR_SUCCESS:
                    return
                elif result == st3215.CommandResult.CR_REJECTED:
                    raise RuntimeError(f"Command rejected: motor {motor_id}, {command_id.hex()}")
                elif result == st3215.CommandResult.CR_FAILED:
                    raise RuntimeError(f"Command failed: motor {motor_id}, {command_id.hex()}")
                # CR_PROCESSING - keep waiting

    async def _wait_for_value(self, bus_serial: str, motor_id: int, address: int, value: bytes):
        """Loop reading state until state[address:address+len] matches value."""
        deadline = time.monotonic() + VERIFY_TIMEOUT_S

        last_seen_value = None

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                if last_seen_value is not None:
                    raise TimeoutError(
                        f"Verify timeout: motor {motor_id} addr 0x{address:02X} expected 0x{value.hex()} but got 0x{last_seen_value.hex()}"
                    )
                else:
                    raise TimeoutError(
                        f"Verify timeout: motor {motor_id} addr 0x{address:02X} expected 0x{value.hex()}"
                    )

            try:
                state = await asyncio.wait_for(
                    self.read_next_state(), timeout=remaining,
                )
            except asyncio.TimeoutError:
                if last_seen_value is not None:
                    raise TimeoutError(
                        f"Verify timeout: motor {motor_id} addr 0x{address:02X} expected 0x{value.hex()} but got 0x{last_seen_value.hex()}"
                    ) from None
                else:
                    raise TimeoutError(
                        f"Verify timeout: motor {motor_id} addr 0x{address:02X} expected 0x{value.hex()}"
                    ) from None

            motor = self._find_motor(state, bus_serial, motor_id)
            if motor is None:
                continue

            motor_bytes = bytes(motor.get_state())
            if len(motor_bytes) >= address + len(value):
                current_value = motor_bytes[address:address + len(value)]
                last_seen_value = current_value
                if current_value == value:
                    return

    async def send_write(self, bus_serial: str, motor_id: int, address: int, value: bytes):
        """Send RAM write and wait for command execution."""
        command_id = await self.send_st3215_command(st3215.Command(
            target_bus_serial=bus_serial,
            write=st3215.ST3215WriteCommand(
                motor_id=motor_id, address=address, value=value,
            ),
        ))
        await self.wait_for_command_result(bus_serial, motor_id, command_id)

    async def send_write_verified(self, bus_serial: str, motor_id: int, address: int, value: bytes):
        """Send RAM write and wait for value to appear in state. Retries up to 5 times on failure."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await self.send_write(bus_serial, motor_id, address, value)
                await self._wait_for_value(bus_serial, motor_id, address, value)
                return  # Success
            except TimeoutError as e:
                if attempt < max_retries - 1:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"RAM write verification failed (attempt {attempt + 1}/{max_retries}): {e}")
                else:
                    raise  # Re-raise on final attempt

    async def send_eeprom_write(self, bus_serial: str, motor_id: int, address: int, value: bytes):
        """Write to EEPROM: unlock -> reg_write -> action -> lock."""
        # Unlock EEPROM
        await self.send_write(bus_serial, motor_id, RAM_LOCK, b'\x00')

        # Send reg_write command
        command_id = await self.send_st3215_command(st3215.Command(
            target_bus_serial=bus_serial,
            reg_write=st3215.ST3215RegWriteCommand(
                motor_id=motor_id, address=address, value=value,
            ),
        ))
        await self.wait_for_command_result(bus_serial, motor_id, command_id)

        # Send action command
        command_id = await self.send_st3215_command(st3215.Command(
            target_bus_serial=bus_serial,
            action=st3215.ST3215ActionCommand(motor_id=motor_id),
        ))
        await self.wait_for_command_result(bus_serial, motor_id, command_id)

        # Lock EEPROM
        await self.send_write(bus_serial, motor_id, RAM_LOCK, b'\x01')

    async def send_eeprom_write_verified(self, bus_serial: str, motor_id: int, address: int, value: bytes):
        """Write to EEPROM and wait for value to appear in state. Retries up to 5 times on failure."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await self.send_eeprom_write(bus_serial, motor_id, address, value)
                await self._wait_for_value(bus_serial, motor_id, address, value)
                return  # Success
            except TimeoutError as e:
                if attempt < max_retries - 1:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"EEPROM write verification failed (attempt {attempt + 1}/{max_retries}): {e}")
                else:
                    raise  # Re-raise on final attempt

    async def set_torque(self, bus_serial: str, motor_id: int, enable: int):
        """Enable (1) or disable (0) motor torque."""
        await self.send_write_verified(
            bus_serial, motor_id, RAM_TORQUE_ENABLE, bytes([enable]),
        )

    async def set_position(self, bus_serial: str, motor_id: int, position: int):
        """Set goal position."""
        await self.send_write_verified(
            bus_serial, motor_id, RAM_GOAL_POSITION, position.to_bytes(2, 'little'),
        )

    async def wait_for_stall(self, bus_serial: str, motor_id: int, motor_positions: dict[int, set[int]]) -> int:
        """Wait until motor stalls and return displayed position."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Motor {motor_id} - Waiting for stall")

        last_stamp = 0
        startup_steps = 0
        stable_count = 0
        first_stale_stamp = None

        while True:
            state = await self.read_next_state()
            motor = self._find_motor(state, bus_serial, motor_id)

            if motor is None:
                continue

            motor_error = motor.get_error()
            if motor_error is not None:
                servo_errors = motor_error.get_servo()
                if servo_errors and len(servo_errors) > 0:
                    logger.warning(f"Motor {motor_id} in error state, recovering")
                    await self.set_torque(bus_serial, motor_id, 0)
                    await self.set_torque(bus_serial, motor_id, 1)
                    continue

            state_bytes = motor.get_state()
            if len(state_bytes) <= EEPROM_OFFSET + 1:
                continue

            current_stamp = motor.get_monotonic_stamp_ns()
            is_fresh = current_stamp > last_stamp

            if is_fresh:
                last_stamp = current_stamp
                startup_steps += 1
            else:
                continue

            velocity = get_velocity(state_bytes)
            displayed_position = get_position(state_bytes)
            offset = get_offset(state_bytes)
            encoder_position = (displayed_position + offset + FULL_RANGE) % FULL_RANGE

            if motor_id not in motor_positions:
                motor_positions[motor_id] = set()
            motor_positions[motor_id].add(encoder_position)

            if startup_steps >= MOTOR_STARTUP_STEPS:
                if not is_fresh and velocity < VELOCITY_THRESHOLD:
                    if first_stale_stamp is None:
                        first_stale_stamp = current_stamp

                    stale_duration_ms = (current_stamp - first_stale_stamp) / 1_000_000
                    if stale_duration_ms >= 100:
                        stable_count += 1
                elif is_fresh:
                    first_stale_stamp = None
                    if velocity < VELOCITY_THRESHOLD:
                        stable_count += 1
                    else:
                        stable_count = 0

                if stable_count > SKIP_INITIAL_SAMPLES:
                    logger.info(f"Motor {motor_id} - Stalled at position {displayed_position}")
                    return displayed_position

    async def find_min(self, bus_serial: str, motor_id: int, torque_after: int, motor_positions: dict[int, set[int]], speed: int, accel: int):
        """Find minimum position by moving toward 0 until stall."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Motor {motor_id} - Finding minimum position")

        # Set speed and acceleration before movement
        await self.send_write_verified(bus_serial, motor_id, RAM_GOAL_SPEED, speed.to_bytes(2, 'little'))
        await self.send_write_verified(bus_serial, motor_id, RAM_ACC, bytes([accel]))

        state = await self.read_next_state()
        motor = self._find_motor(state, bus_serial, motor_id)

        if motor is None:
            raise RuntimeError("Motor not found")

        state_bytes = motor.get_state()
        if len(state_bytes) <= RAM_PRESENT_POSITION + 1:
            raise RuntimeError("Failed to read position")

        displayed = get_position(state_bytes)
        offset = get_offset(state_bytes) if len(state_bytes) > EEPROM_OFFSET + 1 else 0
        current_encoder = (displayed + offset + FULL_RANGE) % FULL_RANGE

        new_offset = current_encoder - (4095 - SAFE_OFFSET)

        if new_offset < -2047:
            new_offset = new_offset + 4096
        elif new_offset > 2047:
            new_offset = new_offset - 4096

        new_offset = max(-2047, min(2047, new_offset))

        await self.send_eeprom_write_verified(
            bus_serial, motor_id, EEPROM_OFFSET, new_offset.to_bytes(2, 'little', signed=True)
        )

        current_target = 4095 - SAFE_OFFSET

        while current_target > 0:
            next_target = current_target - CALIBRATION_STEP if current_target >= CALIBRATION_STEP else 0

            await self.set_position(bus_serial, motor_id, next_target)
            final_pos = await self.wait_for_stall(bus_serial, motor_id, motor_positions)

            if final_pos > next_target + 50:
                logger.info(f"Motor {motor_id} - Found min at {final_pos}")
                break

            current_target = next_target

        await self.set_torque(bus_serial, motor_id, torque_after)

    async def find_max(self, bus_serial: str, motor_id: int, torque_after: int, motor_positions: dict[int, set[int]], speed: int, accel: int):
        """Find maximum position by moving toward 4095 until stall."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Motor {motor_id} - Finding maximum position")

        # Set speed and acceleration before movement
        await self.send_write_verified(bus_serial, motor_id, RAM_GOAL_SPEED, speed.to_bytes(2, 'little'))
        await self.send_write_verified(bus_serial, motor_id, RAM_ACC, bytes([accel]))

        state = await self.read_next_state()
        motor = self._find_motor(state, bus_serial, motor_id)

        if motor is None:
            raise RuntimeError("Motor not found")

        state_bytes = motor.get_state()
        if len(state_bytes) <= RAM_PRESENT_POSITION + 1:
            raise RuntimeError("Failed to read position")

        displayed = get_position(state_bytes)
        offset = get_offset(state_bytes) if len(state_bytes) > EEPROM_OFFSET + 1 else 0
        current_encoder = (displayed + offset + FULL_RANGE) % FULL_RANGE

        new_offset = current_encoder - SAFE_OFFSET

        if new_offset > 2047:
            new_offset = new_offset - 4096
        elif new_offset < -2047:
            new_offset = new_offset + 4096

        new_offset = max(-2047, min(2047, new_offset))

        await self.send_eeprom_write_verified(
            bus_serial, motor_id, EEPROM_OFFSET, new_offset.to_bytes(2, 'little', signed=True)
        )

        current_target = SAFE_OFFSET

        while current_target < 4095:
            next_target = current_target + CALIBRATION_STEP if current_target + CALIBRATION_STEP <= 4095 else 4095

            await self.set_position(bus_serial, motor_id, next_target)
            final_pos = await self.wait_for_stall(bus_serial, motor_id, motor_positions)

            if final_pos < next_target - 50:
                logger.info(f"Motor {motor_id} - Found max at {final_pos}")
                break

            current_target = next_target

        await self.set_torque(bus_serial, motor_id, torque_after)

    async def shift(self, bus_serial: str, motor_id: int, steps: int, torque_after: int, motor_positions: dict[int, set[int]], speed: int, accel: int):
        """Shift motor by specified steps from a safe position."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Motor {motor_id} - Shifting by {steps} steps")

        # Set speed and acceleration before movement
        await self.send_write_verified(bus_serial, motor_id, RAM_GOAL_SPEED, speed.to_bytes(2, 'little'))
        await self.send_write_verified(bus_serial, motor_id, RAM_ACC, bytes([accel]))

        state = await self.read_next_state()
        motor = self._find_motor(state, bus_serial, motor_id)

        if motor is None:
            raise RuntimeError("Motor not found")

        state_bytes = motor.get_state()
        if len(state_bytes) <= RAM_PRESENT_POSITION + 1:
            raise RuntimeError("Failed to read position")

        displayed = get_position(state_bytes)
        offset = get_offset(state_bytes) if len(state_bytes) > EEPROM_OFFSET + 1 else 0
        current_encoder = (displayed + offset + FULL_RANGE) % FULL_RANGE

        start_position = SAFE_OFFSET if steps >= 0 else 4095 - SAFE_OFFSET
        new_offset = current_encoder - start_position

        if new_offset > 2047:
            new_offset = new_offset - 4096
        elif new_offset < -2047:
            new_offset = new_offset + 4096

        new_offset = max(-2047, min(2047, new_offset))

        await self.send_eeprom_write_verified(
            bus_serial, motor_id, EEPROM_OFFSET, new_offset.to_bytes(2, 'little', signed=True)
        )

        target_displayed = max(0, min(4095, start_position + steps))
        step_size = CALIBRATION_STEP
        current_pos = start_position
        direction = 1 if steps > 0 else -1

        while (direction > 0 and current_pos < target_displayed) or (direction < 0 and current_pos > target_displayed):
            if direction > 0:
                next_step = min(current_pos + step_size, target_displayed)
            else:
                next_step = max(current_pos - step_size, target_displayed)

            await self.set_position(bus_serial, motor_id, next_step)
            await self.wait_for_stall(bus_serial, motor_id, motor_positions)
            current_pos = next_step

        await self.set_torque(bus_serial, motor_id, torque_after)

    async def go_to_float_position(self, bus_serial: str, motor_id: int, float_pos: float, torque_after: int, motor_positions: dict[int, set[int]], speed: int, accel: int):
        """Move motor to normalized position (0.0-1.0) within calibrated arc."""
        import logging
        from arc import calculate_arc
        logger = logging.getLogger(__name__)
        logger.info(f"Motor {motor_id} - Moving to float position {float_pos}")

        # Set speed and acceleration before movement
        await self.send_write_verified(bus_serial, motor_id, RAM_GOAL_SPEED, speed.to_bytes(2, 'little'))
        await self.send_write_verified(bus_serial, motor_id, RAM_ACC, bytes([accel]))

        # Clamp float position to [0.0, 1.0]
        float_pos = max(0.0, min(1.0, float_pos))

        # Get recorded positions and calculate arc
        if motor_id not in motor_positions:
            raise RuntimeError("No recorded positions for motor")

        positions = motor_positions[motor_id]
        if not positions:
            raise RuntimeError("No positions recorded during calibration")

        logger.info(f"Motor {motor_id} - Recorded {len(positions)} positions: {sorted(positions)}")

        arc = calculate_arc(positions)

        # Calculate midpoint and range
        if arc.max >= arc.min:
            # Normal range
            range_size = arc.max - arc.min
            midpoint = arc.min + range_size // 2
        else:
            # Wraparound range
            range_size = (4096 - arc.min) + arc.max
            midpoint = (arc.min + range_size // 2) & 0xFFF

        # Calculate offset to center the arc at 2048
        offset = midpoint - 2048
        offset_clamped = max(-2047, min(2047, offset))

        logger.info(f"Motor {motor_id} - Arc: min={arc.min}, max={arc.max}, midpoint={midpoint}, range={range_size}, offset={offset_clamped}")

        # Write offset to EEPROM to center the arc at 2048
        await self.send_eeprom_write_verified(
            bus_serial, motor_id, EEPROM_OFFSET, offset_clamped.to_bytes(2, 'little', signed=True)
        )

        # Calculate goal position in the new offset coordinate system
        goal_offset = int((float_pos - 0.5) * range_size)
        goal_pos = (2048 + goal_offset) & 0xFFF

        logger.info(f"Motor {motor_id} - Float position {float_pos} -> goal position {goal_pos}")

        await self.set_position(bus_serial, motor_id, goal_pos)

        logger.info(f"Motor {motor_id} - Commanded to position {goal_pos}")

        final_pos = await self.wait_for_stall(bus_serial, motor_id, motor_positions)

        logger.info(f"Motor {motor_id} - Reached position {final_pos}")

        await self.set_torque(bus_serial, motor_id, torque_after)

    async def send_reset(self, bus_serial: str, motor_id: int):
        """Send reset command to motor and verify offset becomes 0."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Motor {motor_id} - Sending reset command")

        # Unlock EEPROM
        await self.send_write(bus_serial, motor_id, RAM_LOCK, b'\x00')

        # Send reset command
        command_id = await self.send_st3215_command(st3215.Command(
            target_bus_serial=bus_serial,
            reset=st3215.ST3215ResetCommand(
                port_name=bus_serial,
                motor_id=motor_id,
            ),
        ))
        await self.wait_for_command_result(bus_serial, motor_id, command_id)

        # Lock EEPROM
        await self.send_write(bus_serial, motor_id, RAM_LOCK, b'\x01')

        # Wait for motor to complete reset
        await asyncio.sleep(1)

        # Write offset=0 and verify
        await self.send_eeprom_write_verified(
            bus_serial, motor_id, EEPROM_OFFSET, (0).to_bytes(2, 'little', signed=True)
        )

        logger.info(f"Motor {motor_id} - Reset complete, offset is 0")