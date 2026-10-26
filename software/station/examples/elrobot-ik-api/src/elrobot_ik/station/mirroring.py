"""The station's motors-mirroring state: which buses a leader is currently driven onto.

The mirroring driver publishes a `mirroring.RxEnvelope` to `inference/mirroring` at startup and
after every start/stop command, so the newest entry is the current state.
"""
from elrobot_ik.station import registers as R
from elrobot_ik.station.arms import ELROBOT_MOTOR_IDS
from elrobot_ik.station.proto import mirroring_pb2, st3215_pb2

MIRRORING_QUEUE = "inference/mirroring"


def mirroring_targets(entry: bytes) -> frozenset[str]:
    """Serials of the buses that are mirroring targets (followers driven by a leader) in an entry."""
    env = mirroring_pb2.RxEnvelope.FromString(entry)
    return frozenset(t.id.unique_id for m in env.state.mirroring for t in m.targets)


def torque_release_receipt(frame: bytes | None, serial: str) -> bytes | None:
    """A completed whole-bus torque-off write from the existing mirroring driver.

    That driver uses the bus serial as command_id. The TxEnvelope includes the station's
    timestamp and app_start_id, so a new receipt differs from one retained before our stop.
    Queue-write acknowledgement or an already-disabled torque bit alone is not completion.
    """
    if frame is None:
        return None
    buses = st3215_pb2.InferenceState.FromString(frame).buses
    bus = next((b for b in buses if b.bus.serial_number == serial), None)
    if bus is None or {m.id for m in bus.motors} != set(ELROBOT_MOTOR_IDS):
        return None
    receipts = set()
    for motor in bus.motors:
        last = motor.last_command
        cmd = last.command
        if (last.result != st3215_pb2.CR_SUCCESS or cmd.target_bus_serial != serial
                or cmd.command_id != serial.encode() or not cmd.monotonic_stamp_ns
                or cmd.sync_write.address != R.ADDR_TORQUE_ENABLE
                or {w.motor_id for w in cmd.sync_write.motors} != set(ELROBOT_MOTOR_IDS)
                or any(w.value != b"\x00" for w in cmd.sync_write.motors)):
            return None
        receipts.add(cmd.SerializeToString())
    return receipts.pop() if len(receipts) == 1 else None
