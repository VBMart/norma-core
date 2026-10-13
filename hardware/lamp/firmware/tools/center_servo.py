#!/usr/bin/env python3
"""Make the current output position of an ST3215 read 2048 (the middle of its 0..4095 range).

Pose the lamp by hand (torque off), then:

    py -3 center_servo.py 1 2 3 4 5       # all joints at once
    py -3 center_servo.py 3 --port COM9   # one servo, explicit port

Writing 128 to the torque register (40) makes the servo store the needed value in its
position-correction register (31..32, EEPROM, -2047..2047, bit 11 = sign). The EEPROM is
unlocked and re-locked around the write so the correction survives power off.
Needed when a horn was seated so that the 0/4095 wrap falls inside the working range:
position mode cannot cross it.
"""
import argparse
import sys
import time

from set_servo_id import Bus, pick_port

REG_OFS, REG_TORQUE, REG_LOCK, REG_POS = 31, 40, 55, 56


def word(b):
    return b[0] | (b[1] << 8)


def offset(b):
    v = word(b)
    return -(v & 0x7FF) if v & 0x800 else v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", type=int, nargs="+", help="servo IDs to centre")
    ap.add_argument("--port", help="COM port of the bus adapter (auto if only one)")
    ap.add_argument("--baud", type=int, default=1_000_000)
    a = ap.parse_args()
    bus = Bus(pick_port(a.port), a.baud)
    for sid in a.ids:
        if not bus.ping(sid):
            print(f"id {sid}: no answer, skipped")
            continue
        before, o0 = word(bus.read(sid, REG_POS, 2)), offset(bus.read(sid, REG_OFS, 2))
        bus.write(sid, REG_LOCK, [0]); time.sleep(0.02)
        bus.write(sid, REG_TORQUE, [128]); time.sleep(0.05)
        bus.write(sid, REG_LOCK, [1]); time.sleep(0.02)
        after, o1 = word(bus.read(sid, REG_POS, 2)), offset(bus.read(sid, REG_OFS, 2))
        print(f"id {sid}: pos {before} -> {after}, correction {o0} -> {o1}" + ("" if after == 2048 else "  (NOT centred)"))
    bus.close()


if __name__ == "__main__":
    main()
