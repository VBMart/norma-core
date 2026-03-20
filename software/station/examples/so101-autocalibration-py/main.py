"""SO101 auto-calibration script for ST3215 servos.

Ports the Rust calibration process from:
  software/drivers/st3215/src/auto_calibrate/so101.rs
  software/drivers/st3215/src/auto_calibrate/calibrator.rs

Usage:
  python calibrate_so101.py [--server localhost] [--bus-serial SERIAL]
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from software.station.shared.station_py import new_station_client, send_commands, StreamEntry
from st3215 import (
    EEPROM_MAX_TEMPERATURE, EEPROM_MAX_TORQUE, EEPROM_MODE,
    EEPROM_OFFSET, EEPROM_OVERLOAD_TORQUE, EEPROM_P_COEF,
    EEPROM_I_COEF, EEPROM_D_COEF, EEPROM_PROTECTION_CURRENT,
    EEPROM_RETURN_DELAY,
    RAM_ACC, RAM_GOAL_SPEED,
    RAM_TORQUE_ENABLE, RAM_TORQUE_LIMIT,
    St3215Driver,
    FULL_RANGE, MAX_ANGLE_STEP,
)
from arc import calculate_arc, MotorArc

from target.gen_python.protobuf.station import commands, drivers
from target.gen_python.protobuf.drivers.st3215 import st3215

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# Calibration constants
# =============================================================================

# Motion parameters during calibration
CALIBRATION_SPEED = 365
CALIBRATION_ACCEL = 50
CALIBRATION_TORQUE_LIMIT = 300
CALIBRATION_TEMPERATURE_LIMIT = 45

# Per-motor speeds during calibration (motor 6 moves twice as fast)
MOTOR_SPEEDS = {
    1: CALIBRATION_SPEED,
    2: CALIBRATION_SPEED,
    3: CALIBRATION_SPEED,
    4: CALIBRATION_SPEED,
    5: CALIBRATION_SPEED,
    6: CALIBRATION_SPEED * 2,  # 2x speed
}

# Per-motor acceleration during calibration (motor 6 accelerates twice as fast)
MOTOR_ACCELS = {
    1: CALIBRATION_ACCEL,
    2: CALIBRATION_ACCEL,
    3: CALIBRATION_ACCEL,
    4: CALIBRATION_ACCEL,
    5: CALIBRATION_ACCEL,
    6: CALIBRATION_ACCEL,
}

# Stall detection
VELOCITY_THRESHOLD = 10
SKIP_INITIAL_SAMPLES = 3
MOTOR_STARTUP_STEPS = 4

# Movement
CALIBRATION_STEP = 1020
SAFE_OFFSET = 60

# Default motor settings (restored after calibration)
DEFAULT_MAX_TORQUE = 500
DEFAULT_PROTECTION_CURRENT = 260
DEFAULT_PROTECTION_TEMPERATURE = 65
DEFAULT_OVERLOAD_TORQUE = 25
DEFAULT_ACCEL = 254
DEFAULT_TORQUE_LIMIT = 500
DEFAULT_PID_P = 16
DEFAULT_PID_I = 8
DEFAULT_PID_D = 32

# SO101 robot: 6 motors
MOTOR_IDS = [1, 2, 3, 4, 5, 6]

# Per-motor protection current limits during calibration
MOTOR_CURRENT_LIMITS = {
    1: 50,
    2: 500,
    3: 500,
    4: 50,
    5: 15,
    6: 300,
}

# Per-motor torque limit overrides (only motors that differ from default)
MOTOR_TORQUE_LIMITS = {
    1: DEFAULT_MAX_TORQUE,
    2: DEFAULT_MAX_TORQUE,
    3: DEFAULT_MAX_TORQUE,
    4: DEFAULT_MAX_TORQUE,
    5: 120,
    6: 200,
}

COMMAND_TIMEOUT_S = 10.0
VERIFY_TIMEOUT_S = 10.0
RESET_STABILIZE_DELAY_S = 0.5
EEPROM_WRITE_DELAY_S = 0.5

# =============================================================================
# Calibrator
# =============================================================================

class SO101Calibrator:
    """Calibrates all 6 SO101 servos through the station API."""

    def __init__(self, server: str, bus_serial: str):
        self.server = server
        self.bus_serial = bus_serial
        self.client = None
        self.driver = None
        self.motor_positions: dict[int, set[int]] = {}

    # -------------------------------------------------------------------------
    # Connection & state
    # -------------------------------------------------------------------------

    async def connect(self):
        """Connect to station, start inference subscriber, discover bus."""
        logger.info("Connecting to %s...", self.server)
        self.client = await new_station_client(self.server, logger)
        logger.info("Connected")

        # Create driver (will subscribe to st3215/inference)
        self.driver = St3215Driver(self.client)
        logger.info("Subscribed to st3215/inference")

        # Read first state and validate bus
        state = await self.driver.read_next_state()
        buses = state.get_buses() or []

        if not self.bus_serial:
            # Auto-discover bus
            if len(buses) == 0:
                raise RuntimeError("No bus found on station")
            if len(buses) > 1:
                raise RuntimeError(f"Multiple buses found ({len(buses)}), specify --bus-serial")

            bus = buses[0]
            bus_info = bus.get_bus()
            if bus_info:
                self.bus_serial = bus_info.get_serial_number()
            else:
                raise RuntimeError("No bus info available")

            motors = bus.get_motors() or []
            if len(motors) != 6:
                raise RuntimeError(f"Expected 6 motors on bus {self.bus_serial}, found {len(motors)}")
        else:
            # Validate provided bus_serial exists
            target_bus = None
            for bus in buses:
                bus_info = bus.get_bus()
                if bus_info and bus_info.get_serial_number() == self.bus_serial:
                    target_bus = bus
                    break

            if target_bus is None:
                raise RuntimeError(f"Bus {self.bus_serial} not found on station")

            motors = target_bus.get_motors() or []
            if len(motors) != 6:
                raise RuntimeError(f"Expected 6 motors on bus {self.bus_serial}, found {len(motors)}")

        logger.info("Using bus: %s", self.bus_serial)

    async def reset_calibration(self):
        """Reset calibration bounds on the bus."""
        logger.info("Resetting calibration bounds for bus %s", self.bus_serial)
        await self.driver.send_st3215_command(st3215.Command(
            target_bus_serial=self.bus_serial,
            reset_calibration=st3215.ResetCalibrationCommand(reset=True),
        ))

    async def cleanup_motor(self, motor_id: int):
        """Restore default settings on a motor after calibration."""
        logger.info("Motor %d: Cleaning up", motor_id)

        await self.driver.send_eeprom_write(self.bus_serial, motor_id, EEPROM_MAX_TORQUE,DEFAULT_MAX_TORQUE.to_bytes(2, 'little'))
        await self.driver.send_eeprom_write(self.bus_serial, motor_id, EEPROM_PROTECTION_CURRENT,DEFAULT_PROTECTION_CURRENT.to_bytes(2, 'little'))
        await self.driver.send_eeprom_write(self.bus_serial, motor_id, EEPROM_OVERLOAD_TORQUE, bytes([DEFAULT_OVERLOAD_TORQUE]))
        await self.driver.send_eeprom_write(self.bus_serial, motor_id, EEPROM_OFFSET, b'\x00\x00')
        await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_MAX_TEMPERATURE, bytes([DEFAULT_PROTECTION_TEMPERATURE]))

        await self.driver.send_write(self.bus_serial, motor_id, RAM_GOAL_SPEED, b'\x00\x00')
        await self.driver.send_write(self.bus_serial, motor_id, RAM_ACC, bytes([DEFAULT_ACCEL]))
        await self.driver.send_write(self.bus_serial, motor_id, RAM_TORQUE_LIMIT, DEFAULT_TORQUE_LIMIT.to_bytes(2, 'little'),)

    async def disable_all_torque(self):
        """Disable torque on all motors in one batch."""
        for motor_id in MOTOR_IDS:
            await self.driver.send_write(self.bus_serial, motor_id, RAM_TORQUE_ENABLE, b'\x00')
        logger.info("All motors torque disabled")

    async def cleanup_all_motors(self):
        """Restore default settings on all motors in batches."""
        logger.info("Cleaning up all motors")
        for motor_id in MOTOR_IDS:
            await self.cleanup_motor(motor_id)
        logger.info("All motors cleaned up")

    def print_calibration_summary(self):
        """Print calibrated ranges for all motors."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 CALIBRATION SUMMARY")
        logger.info("=" * 60)
        logger.info("")

        for motor_id in MOTOR_IDS:
            if motor_id not in self.motor_positions or not self.motor_positions[motor_id]:
                logger.warning("Motor %d: No calibration data", motor_id)
                continue

            arc = calculate_arc(self.motor_positions[motor_id])

            # Calculate center and range (handle wrap-around)
            if arc.max >= arc.min:
                # Normal/direct arc
                range_size = arc.max - arc.min
                center = arc.min + range_size // 2
            else:
                # Wrap-around arc
                range_size = (FULL_RANGE - arc.min) + arc.max
                center = (arc.min + range_size // 2) & MAX_ANGLE_STEP

            logger.info("Motor %d:", motor_id)
            logger.info("  Min:    %4d", arc.min)
            logger.info("  Max:    %4d", arc.max)
            logger.info("  Center: %4d", center)
            logger.info("  Range:  %4d", range_size)
            logger.info("")

    async def save_calibration(self):
        """Save calibration by sending freeze command with motor arcs to station."""
        logger.info("Saving calibration for bus %s", self.bus_serial)

        # Build motor arcs from calibration data
        motor_arcs = []
        for motor_id in MOTOR_IDS:
            if motor_id not in self.motor_positions or not self.motor_positions[motor_id]:
                logger.warning("Motor %d: No calibration data, skipping", motor_id)
                continue

            arc = calculate_arc(self.motor_positions[motor_id])

            # Calculate midpoint (handle wrap-around)
            if arc.max >= arc.min:
                # Normal/direct arc
                range_size = arc.max - arc.min
                midpoint = arc.min + range_size // 2
            else:
                # Wrap-around arc
                range_size = (FULL_RANGE - arc.min) + arc.max
                midpoint = (arc.min + range_size // 2) & MAX_ANGLE_STEP

            logger.info("Motor %d: Sending arc min=%d max=%d midpoint=%d",
                       motor_id, arc.min, arc.max, midpoint)

            # Create FreezeMotorArc
            motor_arc = st3215.FreezeMotorArc(
                motor_id=motor_id,
                min_angle=arc.min,
                max_angle=arc.max,
                midpoint=midpoint
            )
            motor_arcs.append(motor_arc)

        # Send freeze command with arcs
        await self.driver.send_st3215_command(st3215.Command(
            target_bus_serial=self.bus_serial,
            freeze_calibration=st3215.FreezeCalibrationCommand(
                freeze=True,
                arcs=motor_arcs
            ),
        ))
        logger.info("Calibration freeze command sent with %d motor arcs", len(motor_arcs))

    async def prepare_motors(self, motor_ids: list[int]):
        """Reset and configure all motors for calibration."""
        # Reset all motors sequentially (each needs stabilize delay)
        for motor_id in motor_ids:
            logger.info("Motor %d: Preparing", motor_id)
            await self.driver.send_reset(self.bus_serial, motor_id)

            await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_MODE, b'\x00')
            await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_P_COEF, bytes([DEFAULT_PID_P]))
            await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_I_COEF, bytes([DEFAULT_PID_I]))
            await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_D_COEF, bytes([DEFAULT_PID_D]))
            await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_RETURN_DELAY, b'\x00')
            await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_MAX_TEMPERATURE, bytes([CALIBRATION_TEMPERATURE_LIMIT]))
            await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_MAX_TORQUE, CALIBRATION_TORQUE_LIMIT.to_bytes(2, 'little'))
            await self.driver.send_eeprom_write_verified(self.bus_serial, motor_id, EEPROM_PROTECTION_CURRENT, MOTOR_CURRENT_LIMITS[motor_id].to_bytes(2, 'little'))

            # Configure RAM registers
            await self.driver.send_write_verified(self.bus_serial, motor_id, RAM_TORQUE_ENABLE, b'\x00')
            await self.driver.send_write_verified(self.bus_serial, motor_id, RAM_GOAL_SPEED, MOTOR_SPEEDS[motor_id].to_bytes(2, 'little'))
            await self.driver.send_write_verified(self.bus_serial, motor_id, RAM_ACC, bytes([MOTOR_ACCELS[motor_id]]))
            await self.driver.send_write_verified(self.bus_serial, motor_id, RAM_TORQUE_LIMIT, MOTOR_TORQUE_LIMITS[motor_id].to_bytes(2, 'little'))

            logger.info("Motor %d configured", motor_id)

        logger.info("All motors ready")

    # -------------------------------------------------------------------------
    # Flow control
    # -------------------------------------------------------------------------

    async def run(self):
        """Execute the full SO101 calibration sequence."""

        # Step 0: Reset calibration bounds, then prepare all motors
        logger.info("=" * 60)
        logger.info("🔧 PREPARING ALL MOTORS")
        logger.info("=" * 60)
        await self.reset_calibration()
        await self.prepare_motors(MOTOR_IDS)

        # Steps 1-3: Motor 1
        logger.info("=" * 60)
        logger.info("🤖 MOTOR 1 CALIBRATION")
        logger.info("=" * 60)
        await self.driver.find_max(self.bus_serial, 1, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[1], accel=MOTOR_ACCELS[1])
        await self.driver.find_min(self.bus_serial, 1, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[1], accel=MOTOR_ACCELS[1])
        await self.driver.go_to_float_position(self.bus_serial, 1, 0.5, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[1], accel=MOTOR_ACCELS[1])

        # Step 4: Motor 2
        logger.info("=" * 60)
        logger.info("🤖 MOTORS 2-6 INITIAL CALIBRATION")
        logger.info("=" * 60)
        await self.driver.find_min(self.bus_serial, 2, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[2], accel=MOTOR_ACCELS[2])

        # Step 5: Motor 3
        await self.driver.find_max(self.bus_serial, 3, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[3], accel=MOTOR_ACCELS[3])

        # Steps 6-8: Motor 4
        await self.driver.find_max(self.bus_serial, 4, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[4], accel=MOTOR_ACCELS[4])
        await self.driver.find_min(self.bus_serial, 4, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[4], accel=MOTOR_ACCELS[4])
        await self.driver.go_to_float_position(self.bus_serial, 4, 0.5, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[4], accel=MOTOR_ACCELS[4])

        # Steps 9-10: Motor 5
        await self.driver.find_max(self.bus_serial, 5, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[5], accel=MOTOR_ACCELS[5])
        await self.driver.find_min(self.bus_serial, 5, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[5], accel=MOTOR_ACCELS[5])

        # Steps 11-12: Motor 6
        await self.driver.find_max(self.bus_serial, 6, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[6], accel=MOTOR_ACCELS[6])
        await self.driver.find_min(self.bus_serial, 6, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[6], accel=MOTOR_ACCELS[6])

        # Step 13: Increase Motor 3 torque for second pass
        logger.info("=" * 60)
        logger.info("⚡ MOTOR 3 SECOND PASS - INCREASED TORQUE")
        logger.info("=" * 60)
        await self.driver.send_eeprom_write_verified(
            self.bus_serial, 3, EEPROM_MAX_TORQUE, (300).to_bytes(2, 'little'),
        )
        await self.driver.send_write_verified(
            self.bus_serial, 3, RAM_TORQUE_LIMIT, (300).to_bytes(2, 'little'),
        )

        # Steps 14-15: Motor 3 second pass
        logger.info("Motor 3: Find minimum")
        await self.driver.find_min(self.bus_serial, 3, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[3], accel=MOTOR_ACCELS[3])
        logger.info("Motor 3: Shift")
        await self.driver.shift(self.bus_serial, 3, steps=1500, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[3], accel=MOTOR_ACCELS[3])

        # Steps 16-18: Motor 4 re-calibrate
        logger.info("=" * 60)
        logger.info("🔄 MOTOR 4 & 2 ADJUSTMENTS")
        logger.info("=" * 60)
        await self.driver.find_max(self.bus_serial, 4, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[4], accel=MOTOR_ACCELS[4])
        await self.driver.find_min(self.bus_serial, 4, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[4], accel=MOTOR_ACCELS[4])
        await self.driver.go_to_float_position(self.bus_serial, 4, 0.1, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[4], accel=MOTOR_ACCELS[4])

        # Step 19: Motor 2 shift
        await self.driver.shift(self.bus_serial, 2, steps=1216, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[2], accel=MOTOR_ACCELS[2])

        # Steps 20-21: Second pass
        logger.info("=" * 60)
        logger.info("🔁 MOTORS 2 & 3 SECOND PASS")
        logger.info("=" * 60)
        await self.driver.find_min(self.bus_serial, 3, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[3], accel=MOTOR_ACCELS[3])
        await self.driver.find_max(self.bus_serial, 2, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[2], accel=MOTOR_ACCELS[2])

        # Steps 22-23: Center motors 2 and 3
        logger.info("=" * 60)
        logger.info("🎯 CENTERING MOTORS 2 & 3")
        logger.info("=" * 60)
        await self.driver.go_to_float_position(self.bus_serial, 2, 0.5, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[2], accel=MOTOR_ACCELS[2])
        await self.driver.go_to_float_position(self.bus_serial, 3, 0.5, torque_after=1, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[3], accel=MOTOR_ACCELS[3])

        # Steps 24-26: Final positioning
        logger.info("=" * 60)
        logger.info("🏁 FINAL POSITIONING")
        logger.info("=" * 60)
        await self.driver.find_min(self.bus_serial, 2, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[2], accel=MOTOR_ACCELS[2])
        await self.driver.find_max(self.bus_serial, 3, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[3], accel=MOTOR_ACCELS[3])
        await self.driver.go_to_float_position(self.bus_serial, 4, 0.7, torque_after=0, motor_positions=self.motor_positions, speed=MOTOR_SPEEDS[4], accel=MOTOR_ACCELS[4])

        # # Step 27: Disable torque on all motors
        logger.info("=" * 60)
        logger.info("💾 SAVING CALIBRATION")
        logger.info("=" * 60)
        await self.disable_all_torque()

        # # Step 28: Save — cleanup all motors, freeze calibration
        await self.cleanup_all_motors()

        # Print calibration summary
        self.print_calibration_summary()

        await self.save_calibration()

        logger.info("Calibration complete!")


# =============================================================================
# Entry point
# =============================================================================

async def main_async(server: str, bus_serial: str):
    calibrator = SO101Calibrator(server, bus_serial)
    await calibrator.connect()
    try:
        await calibrator.run()
    except Exception:
        logger.exception("Calibration failed")
        try:
            await calibrator.disable_all_torque()
        except Exception:
            logger.exception("Failed to disable torque")
        try:
            await calibrator.cleanup_all_motors()
        except Exception:
            logger.exception("Failed to cleanup motors")
        raise


def main():
    parser = argparse.ArgumentParser(description="SO101 auto-calibration")
    parser.add_argument(
        "--server", default="localhost", help="Station server address",
    )
    parser.add_argument(
        "--bus-serial", default="", help="Bus serial (empty = first bus)",
    )
    args = parser.parse_args()
    asyncio.run(main_async(args.server, args.bus_serial))


if __name__ == "__main__":
    main()