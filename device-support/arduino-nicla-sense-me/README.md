# Nicla Sense ME station firmware

Exposes all BHY2 sensor outputs of an Arduino Nicla Sense ME as a 168-byte
register map for the norma-core station `arduino-nicla-sense-me` driver, over
two transports:

- **I2C** (address `0x22`): wire the board to the Portenta X8 I2C bus via the
  ESLOV connector or the castellated I2C pins. The driver polls at the
  configured `poll-interval` (default 1 s).
- **USB serial**: plug the board into the X8 over USB. The firmware streams a
  snapshot every 10 ms (~100 Hz); see [USB serial transport](#usb-serial-transport).

I2C protocol: write one byte to set the register pointer; subsequent reads
return sequential bytes. Writing pointer `0x00` latches a consistent snapshot
of all values — the station driver reads the full 168-byte map in 32-byte
chunks and always starts at `0x00`, so every dump is internally consistent.
The `sample counter` register (0x01) increments per firmware refresh while
BHY2 is running.

## Register map (little-endian)

| Offset | Size | Field |
|---|---|---|
| 0x00 | u8 | status (bit0 BHY2 ok, bit1 BSEC valid, bit2 rotation vector valid — euler/gravity/linear-accel are zeroed while clear) |
| 0x01 | u8 | sample counter (increments per firmware refresh while BHY2 is running) |
| 0x02–0x0B | — | reserved (zero) |
| 0x0C | u8 | software revision |
| 0x0D | u8 | product id = 0x4D |
| 0x0E–0x13 | 6 B | serial number (nRF52 FICR device id) |
| 0x14 | 3×f32 | accelerometer x, y, z (g) |
| 0x20 | 3×f32 | gyroscope x, y, z (dps) |
| 0x2C | 3×f32 | magnetometer x, y, z (µT) |
| 0x38 | 3×f32 | linear acceleration x, y, z (g) |
| 0x44 | 3×f32 | gravity x, y, z (g) |
| 0x50 | 5×f32 | quaternion w, x, y, z, accuracy |
| 0x64 | 3×f32 | euler heading, pitch, roll (°) |
| 0x70 | f32 | temperature (°C) |
| 0x74 | f32 | humidity (%RH) |
| 0x78 | f32 | pressure (hPa) |
| 0x7C | f32 | gas resistance (Ω) |
| 0x80 | f32 | BSEC IAQ |
| 0x84 | f32 | BSEC static IAQ |
| 0x88 | f32 | BSEC eCO2 (ppm) |
| 0x8C | f32 | BSEC bVOC equivalent |
| 0x90 | f32 | BSEC accuracy (0–3 as f32) |
| 0x94 | f32 | BSEC compensated temperature (°C) |
| 0x98 | f32 | BSEC compensated humidity (%RH) |
| 0x9C | 4 B | reserved (zero) |
| 0xA0 | u32 | step count |
| 0xA4 | u32 | activity recognition bitfield |
| — | — | total length 0xA8 (168 bytes) |

## USB serial transport

The sketch serves a command protocol over the board's USB CDC serial port at
921600 baud. The Nicla's USB port is a SAMD11 serial-to-USB bridge, so the
baud is a real UART rate: it directly limits throughput and must match the
station driver's `SERIAL_BAUD`.

### Command 0x01: Register dump

Send the single byte `0x01`; the reply is one 172-byte frame: magic `0xA5 0x5A`,
length byte `0xA8`, the 168-byte register image (latched, internally consistent),
and a trailing CRC8 (poly 0x07, init 0x00) over the 168-byte payload.
While streaming is active the command is ignored: the pushed frame is the reply.

Used by the probe/bench examples; the station driver uses streaming instead.

### Commands 0x02 / 0x03: Streaming

`0x02` starts streaming: the sketch pushes one frame per 10 ms tick (the
firmware refresh rate — a steady ~100 Hz) in the same CRC8-framed format.
`0x02` also acts as the keepalive: streaming expires unless it is repeated
within 2 s, so a dead host cannot leave the board transmitting. `0x03`
stops streaming immediately. The RGB LED glows red while streaming is
active. Unknown command bytes are ignored.

Hosts should send `0x03` when they open the port (a previous host may have
left the board streaming) and scan for the magic rather than assume a
frame starts at the first byte; the station driver and the examples do
both. Frames whose length or CRC fail are discarded and the scan resumes at
the next byte.

## Flashing

Flashing is done from a workstation over USB (not from the X8).

### macOS

```bash
brew install arduino-cli
arduino-cli core update-index
arduino-cli core install arduino:mbed_nicla
arduino-cli lib install Arduino_BHY2 ArduinoBLE
arduino-cli board list                  # plug the Nicla in via USB; note the port, e.g. /dev/cu.usbmodem14101
arduino-cli compile --fqbn arduino:mbed_nicla:nicla_sense device-support/arduino-nicla-sense-me
arduino-cli upload -p /dev/cu.usbmodem14101 --fqbn arduino:mbed_nicla:nicla_sense device-support/arduino-nicla-sense-me
```

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh   # installs to ./bin
export PATH="$PWD/bin:$PATH"
arduino-cli core update-index
arduino-cli core install arduino:mbed_nicla   # also installs udev rules; re-plug the board afterwards
arduino-cli lib install Arduino_BHY2 ArduinoBLE
arduino-cli board list                  # note the port, e.g. /dev/ttyACM0
arduino-cli compile --fqbn arduino:mbed_nicla:nicla_sense device-support/arduino-nicla-sense-me
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:mbed_nicla:nicla_sense device-support/arduino-nicla-sense-me
```

If the upload fails with "port busy" or the board isn't listed, double-tap the
reset button to enter the bootloader (the LED pulses) and retry the upload.

## Verifying

Over I2C from the X8, with the board wired to bus 2 (adjust as needed):

```bash
i2cdetect -y 2                          # expect a device at 0x22
i2ctransfer -y 2 w1@0x22 0x0c r2        # expect: firmware revision, then 0x4d (product id)
```

Over USB from any host with the board plugged in (the driver crate ships
diagnostics as cargo examples):

```bash
cargo run -p arduino-nicla-sense-me --example usb_probe          # one dump: product id, status, environment
cargo run -p arduino-nicla-sense-me --example stream_bench       # 10 s of streaming: frame rate, CRC failures
cargo run -p arduino-nicla-sense-me --example poll_bench         # back-to-back 0x01 dumps: round-trip latency
cargo run -p arduino-nicla-sense-me --example orientation_probe  # quaternion vs euler vs accel-implied attitude
cargo run -p arduino-nicla-sense-me --example serial_monitor     # raw port bytes for 15 s (boot markers, fault dumps)
```

## Station configuration

```yaml
drivers:
  arduino-nicla-sense-me:
    enabled: true
    poll-interval: 1s               # driver-wide I2C poll interval; USB boards stream and ignore it
    boards:
      - id: nicla-usb
        bus-type: usb               # autodetected by USB vid/pid 2341:0060
        # usb-port: /dev/ttyACM0    # pin a port; required to tell multiple USB boards apart
      - id: imu-front
        bus-type: i2c               # the default
        i2c-bus: 2
        poll-interval: 100ms        # per-board override
```
