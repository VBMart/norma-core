#!/usr/bin/env python3
"""Give each ST3215 servo its own bus ID, one servo at a time.

Plug ONE servo into the bus adapter (USB to the PC, 12 V to the adapter), then:

    py -3 set_servo_id.py                 # interactive: walks through IDs 1..5
    py -3 set_servo_id.py --ids 1 2 3 4 5 # same, explicit list
    py -3 set_servo_id.py --scan          # only show what is on the bus
    py -3 set_servo_id.py --id 3          # set the one connected servo to ID 3
    py -3 set_servo_id.py --port COM7     # pick the port by hand

Protocol: Feetech STS/SMS, FF FF ID LEN INSTR PARAMS... CHK (same as firmware/esp32/src/feetech.h).
"""
import argparse
import sys
import time

import serial
from serial.tools import list_ports

INST_PING, INST_READ, INST_WRITE = 1, 2, 3
REG_MODEL, REG_ID, REG_BAUD, REG_LOCK = 3, 5, 6, 55
BAUDS = [1_000_000, 500_000, 115_200]      # factory default first
SCAN_RANGE = range(1, 11)                   # the IDs the motors might have now


class Bus:
    def __init__(self, port, baud):
        self.s = serial.Serial(port, baud, timeout=0.02, write_timeout=0.2)
        self.baud = baud

    def close(self):
        self.s.close()

    def _tx(self, sid, instr, params):
        pkt = bytes([0xFF, 0xFF, sid, len(params) + 2, instr]) + bytes(params)
        pkt += bytes([(~sum(pkt[2:])) & 0xFF])
        self.s.reset_input_buffer()
        self.s.write(pkt)
        self.s.flush()
        return pkt

    def _rx(self, sent, timeout=0.03):
        """Read one status packet. Half-duplex adapters echo what we send, so the
        echo (if present) is skipped first."""
        deadline = time.monotonic() + timeout
        buf = b""
        while time.monotonic() < deadline:
            buf += self.s.read(64)
            if buf.startswith(sent):
                buf = buf[len(sent):]
                sent = b""
            i = buf.find(b"\xff\xff")
            if i < 0:
                continue
            p = buf[i:]
            if len(p) >= 4 and len(p) >= p[3] + 4:
                p = p[: p[3] + 4]
                if (~sum(p[2:-1])) & 0xFF == p[-1]:
                    return p
                buf = buf[i + 2:]
        return None

    def ping(self, sid):
        p = self._rx(self._tx(sid, INST_PING, []))
        return p is not None and p[2] == sid

    def read(self, sid, reg, n):
        p = self._rx(self._tx(sid, INST_READ, [reg, n]))
        if p is None or p[2] != sid or p[3] != n + 2:
            return None
        return p[5:5 + n]

    def write(self, sid, reg, data):
        self._rx(self._tx(sid, INST_WRITE, [reg] + list(data)))
        time.sleep(0.01)

    def scan(self, ids=SCAN_RANGE):
        return [i for i in ids if self.ping(i)]

    def info(self, sid):
        m = self.read(sid, REG_MODEL, 2)
        model = m[0] | (m[1] << 8) if m else None
        return f"id {sid}, model {model}, {self.baud} baud"

    def set_id(self, old, new):
        self.write(old, REG_LOCK, [0])      # unlock EEPROM
        self.write(old, REG_ID, [new])      # servo answers to `new` from here on
        self.write(new, REG_LOCK, [1])      # lock EEPROM so the ID survives power off
        rb = self.read(new, REG_ID, 1)
        return self.ping(new) and rb is not None and rb[0] == new


def pick_port(name):
    if name:
        return name
    ports = list(list_ports.comports())
    if not ports:
        sys.exit("No serial port found. Plug the bus adapter in (USB) and try again.")
    if len(ports) == 1:
        print(f"Using {ports[0].device} ({ports[0].description})")
        return ports[0].device
    print("Several ports found, pick one with --port:")
    for p in ports:
        print(f"  {p.device}  {p.description}")
    sys.exit(1)


def open_bus(port, baud):
    """Open at the given baud, or try the usual ones until a servo answers."""
    for b in ([baud] if baud else BAUDS):
        bus = Bus(port, b)
        if bus.scan():
            return bus
        bus.close()
    return Bus(port, baud or BAUDS[0])


def find_one(bus):
    found = bus.scan()
    if len(found) == 1:
        return found[0]
    if not found:
        print("  no servo answered on IDs 1..10 (check 12 V power, the cable, and that only the adapter is on the bus)")
    else:
        print(f"  {len(found)} servos answered (IDs {found}); connect only one at a time")
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", help="COM port of the bus adapter (auto if only one)")
    ap.add_argument("--baud", type=int, help="bus baud (default: try 1000000, 500000, 115200)")
    ap.add_argument("--scan", action="store_true", help="list the servos on the bus and exit")
    ap.add_argument("--id", type=int, help="set the single connected servo to this ID and exit")
    ap.add_argument("--ids", type=int, nargs="+", default=[1, 2, 3, 4, 5], help="IDs to assign, one servo each")
    a = ap.parse_args()

    bus = open_bus(pick_port(a.port), a.baud)
    try:
        if a.scan:
            found = bus.scan(range(0, 254))
            print("Servos on the bus:" if found else "No servo answered.")
            for sid in found:
                print("  " + bus.info(sid))
            return

        if a.id is not None:
            old = find_one(bus)
            if old is None:
                sys.exit(1)
            print(f"  found {bus.info(old)}")
            print(f"  {old} -> {a.id}: " + ("OK" if bus.set_id(old, a.id) else "FAILED"))
            return

        print(f"Assigning IDs {a.ids}, one servo at a time. Ctrl+C to stop.")
        for new in a.ids:
            while True:
                input(f"\nConnect the servo that should become ID {new}, then press Enter...")
                old = find_one(bus)
                if old is None:
                    continue
                print(f"  found {bus.info(old)}")
                if old == new:
                    print(f"  already ID {new}, nothing to do")
                    break
                if bus.set_id(old, new):
                    print(f"  {old} -> {new}: OK (saved to EEPROM)")
                    break
                print(f"  {old} -> {new}: FAILED, servo still answers as {bus.scan()}; try again")
        print("\nDone. Unplug the last servo; all five now have their own ID.")
    finally:
        bus.close()


if __name__ == "__main__":
    main()
