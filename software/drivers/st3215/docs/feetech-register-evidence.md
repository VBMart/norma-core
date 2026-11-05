# Feetech STS register addresses: evidence and hardware check

Collected 2026-11-02 for the SO-ARM 102 question (STS3215 / STS3235 / STS3250 on one bus).
Every claim below is backed by a primary source that was downloaded and read, not quoted from memory.
Section 4 is the procedure to confirm on real motors.

## 1. The five addresses in dispute

| Address | Official Feetech meaning | What `src/protocol/memory.rs` calls it today |
|---|---|---|
| 0x00 (0) | firmware major version, 1 B, read-only | `ModelNumber` (2 B) |
| 0x01 (1) | firmware minor version, 1 B, read-only | (second byte of `ModelNumber`) |
| 0x02 (2) | END, endianness flag, 1 B, read-only, value 0 | `FirmwareVersion` |
| 0x03 (3) | servo major version, 1 B = model number low byte | not defined |
| 0x04 (4) | servo minor version, 1 B = model number high byte | not defined |
| 0x12 (18) | Phase, special-function bits | `UnloadCondition` |
| 0x13 (19) | Unload condition, default 44 | `LedAlarm` |
| 0x14 (20) | LED alarm condition, default 47 | not defined |
| 0x18 (24) | minimum startup force, 1 B | `MinStartupForce` (2 B) |
| 0x19 (25) | integral limit, 1 B | (second byte of `MinStartupForce`) |

Everything from 0x05 (ID) through 0x11 (max torque) and from 0x15 (P) onward except 0x18/0x19 matches the official table.
None of the mislabeled entries are referenced by driver code; the risk is only to whoever reads the enum.

## 2. Sources

### 2a. Feetech official memory table (magnetic encoder, SMS & STS)

File: `舵机协议内存表-磁编码版本.xlsx`, sheet `磁编码SMS&STS`, header "SMServo2.40-STM32-485(190225).bin (固件版本：2.43)", revision 220328.
Download page: https://www.feetechrc.com/en/letter-of-agreement.html (entry "Servo Protocol Memory Table - Magnetic Encoding Version").
Direct URL used: `https://www.feetechrc.com/Data/feetechrc/upload/file/20240702/舵机协议内存表-磁编码版本.xlsx`

Rows as they appear (DEC | HEX | function | bytes | default | area | access | min | max | unit):

```
0  | 0    | 固件主版本号 (firmware major)      | 1 |     | EPROM | 只读 (RO)
1  | 1    | 固件次版本号 (firmware minor)      | 1 |     | EPROM | 只读
2  | 2    | END                               | 1 | 0   | EPROM | 只读
3  | 3    | 舵机主版本号 (servo major version) | 1 |     | EPROM | 只读
4  | 4    | 舵机次版本号 (servo minor version) | 1 |     | EPROM | 只读
5  | 0x5  | ID                                | 1 | 1   | EPROM | 读写 | 0 | 253
...
18 | 0x12 | 相位 (Phase)                      | 1 |     | EPROM | 读写 | 0 | 254 | special byte, do not modify
19 | 0x13 | 卸载条件 (Unload condition)        | 1 | 44  | EPROM | 读写 | 0 | 254
20 | 0x14 | LED报警条件 (LED alarm condition)  | 1 | 47  | EPROM | 读写 | 0 | 254
21 | 0x15 | 位置环P                            | 1
22 | 0x16 | 位置环D                            | 1
23 | 0x17 | 位置环I                            | 1
24 | 0x18 | 最小启动力 (min startup force)      | 1 |     | EPROM | 读写 | 0 | 254 | 0.001
25 | 0x19 | 积分限制值 (integral limit)         | 1 |     | EPROM | 读写 | 0 | 254
...
28 | 0x1C | 保护电流 (protection current)       | 2 |     | EPROM | 读写 | 0 | 511 | 6.5 mA
69 | 0x45 | 当前电流 (present current)          | 2 | 0   | SRAM  | 只读 |   |     | 6.5 mA
```

Sheet `特殊字节设置说明` (special byte bits), address 18 (Phase):

```
BIT7 servo direction | BIT6 PWM mode | BIT5 voltage sampling | BIT4 feedback mode (single turn / full angle)
BIT3 speed mode | BIT2 speed unit | BIT1 drive bridge: (0) 无刷马达 brushless, (1) 有刷马达 brushed | BIT0 phase sign
```

The "servo major/minor version" pair at 3-4 is what every SDK reads as the 16-bit little-endian model number.

### 2b. Feetech official Python SDK (`feetech-servo-sdk` 1.0.0, package `scservo_sdk`)

`scservo_sdk/protocol_packet_handler.py`, `ping()`:

```python
data_read, result, error = self.readTxRx(port, scs_id, 3, 2)  # Address 3 : Model Number
if result == COMM_SUCCESS:
    model_number = SCS_MAKEWORD(data_read[0], data_read[1])
```

`scservo_sdk/scservo_def.py`:

```python
INST_PING = 1
INST_READ = 2
INST_WRITE = 3
INST_REG_WRITE = 4
INST_ACTION = 5
INST_SYNC_WRITE = 131  # 0x83
INST_SYNC_READ = 130   # 0x82
```

### 2c. Feetech protocol manual, magnetic-encoder edition (`舵机协议手册-磁编码版本.pdf`, 9 pages)

Instruction table, section 1.3:

```
PING            0x01    READ DATA   0x02    WRITE DATA  0x03    REG WRITE  0x04
ACTION          0x05    SYNC READ   0x82    SYNC WRITE  0x83
RECOVERY        0x06  (restore control table to factory values)
RESET           0x0A  (reset servo state / turn count)
```

Section 1.0 states this series is little-endian: "低字节在前高字节在后". The English SCS/SMS manual (Seeed mirror) confirms SMS is low-byte-first and SCS is high-byte-first.

### 2d. LeRobot v0.6.1, `src/lerobot/motors/feetech/tables.py`

```python
FIRMWARE_MAJOR_VERSION = (0, 1)
FIRMWARE_MINOR_VERSION = (1, 1)
MODEL_NUMBER = (3, 2)
...
"Phase": (18, 1),
"Unloading_Condition": (19, 1),
"LED_Alarm_Condition": (20, 1),
...
MODEL_NUMBER_TABLE = {"sts3215": 777, "sts3250": 2825, "sm8512bl": 11272, "scs0009": 1284}
```

`src/lerobot/motors/motors_bus.py`, `_assert_motors_exist()`: pings each ID, compares the returned model number with the expected one, raises "Motors with incorrect model numbers" or "Missing motor IDs".

### 2e. rustypot (pollen-robotics), `src/servo/feetech/sts3215.rs` and `src/servo/mod.rs`

```rust
reg: (firmware_major_version, r, 0, u8, None),
reg: (firmware_minor_version, r, 1, u8, None),
reg: (model_number, r, 3, u16, None),
reg: (phase, rw, 18, u8, None),
reg: (unloading_condition, rw, 19, u8, None),
reg: (led_alarm_condition, rw, 20, u8, None),
...
(STS3215, 777), // Bytes 9, 3 at address 3, read little-endian (STS byte order)
(STS3235, 2057),
(STS3250, 2825),
```

### 2f. Robonine SO-ARM-102-Lerobot plugin, `tests/test_feetech.py`

The simulated bus the plugin is tested against lays the registers out exactly this way:

```python
for id_, model in enumerate((2057, 2825, 2825, 2057, 777, 777), 1):
    registers = bytearray(256)
    registers[0:2] = bytes([3, 1])                 # firmware 3.1
    registers[3:5] = model.to_bytes(2, "little")   # model number
```

and `assert bus.ping(1) == 2057`.

## 3. Model numbers

| Model | Decimal | Hex | Bytes on the wire at 0x03, 0x04 |
|---|---|---|---|
| STS3215 | 777 | 0x0309 | 09 03 |
| STS3235 | 2057 | 0x0809 | 09 08 |
| STS3250 | 2825 | 0x0B09 | 09 0B |
| STS3036 | 521 | 0x0209 | 09 02 |
| SM8512BL | 11272 | 0x2C08 | 08 2C |
| SCS0009 | 1284 | 0x0504 | 04 05 (SCS is big-endian) |

Sources: LeRobot tables (3215, 3250, 8512, 0009), rustypot mod.rs and README (3235, 3036), Robonine plugin (3235).

## 4. Hardware check

Checksum = ~(ID + Length + Instruction + Params...) & 0xFF. The routine below was verified against the manual's example 2 (`FF FF 01 04 02 38 02 BE` and reply `FF FF 01 04 00 18 05 DD`).

Raw packets for motor ID 1 at 1 000 000 baud, 8N1:

| Purpose | Send | Expect |
|---|---|---|
| PING | `FF FF 01 02 01 FB` | `FF FF 01 02 00 FC` |
| READ model, 2 B at 0x03 | `FF FF 01 04 02 03 02 F3` | STS3215 `FF FF 01 04 00 09 03 EE`, STS3235 `... 09 08 E9`, STS3250 `... 09 0B E6` |
| READ version block, 5 B at 0x00 | `FF FF 01 04 02 00 05 F3` | `FF FF 01 07 00 <fwMaj> <fwMin> 00 <modelLo> <modelHi> <chk>` |
| READ phase/unload/LED, 3 B at 0x12 | `FF FF 01 04 02 12 03 E3` | `FF FF 01 05 00 <phase> 2C 2F <chk>` on factory settings |

What proves what:

- Byte 2 reads 0 and bytes 3-4 read `09 xx` with xx in {03, 08, 0B}: address 3 is the model number, address 0-1 is not.
- Bytes 0-1 are small numbers like `03 01` or `02 36` on every motor: firmware major.minor, as the plugin and rustypot assume.
- Address 0x13 reads 44 (0x2C) and 0x14 reads 47 (0x2F) on an untouched servo: those are the Unload and LED defaults from the official table, so 0x12 is Phase, not Unload.
- On an STS3250, Phase bit 1 should read 0 (brushless); on STS3215/3235 it should read 1 (brushed). This is the one register that differs per model and must not be copied between them.

Run the repo's own protocol code against a port:

```bash
cargo run -p st3215 --example probe_registers -- /dev/cu.usbmodemXXXX 1 2 3 4 5 6
```

The example is `examples/probe_registers.rs` next to this file. It only sends PING and READ; it writes nothing.
