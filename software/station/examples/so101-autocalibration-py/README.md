# SO101 Auto-Calibration - Python API Demo

Demonstrates the Station Python API for controlling ST3215 servo motors:
- **Subscribing to motor state streams** - Real-time position, velocity, temperature
- **Sending commands to motors** - Register writes, position control
- **Zero external dependencies** - Uses only Python standard library and generated protobuf code

## Python API Usage

### 1. Connect to Station

```python
from software.station.shared.station_py import new_station_client

client = await new_station_client(server_address, logger)
```

### 2. Subscribe to Motor States

```python
inference_queue = asyncio.Queue()
error_queue = client.follow("st3215/inference", inference_queue)

# Read state entries
entry = await inference_queue.get()
state = st3215.InferenceStateReader(entry.Data)
```

### 3. Send Commands

```python
from software.station.shared.station_py import send_commands
from target.gen_python.protobuf.station import commands

driver_cmd = commands.DriverCommand(
    command_id=command_id,
    type=drivers.StationCommandType.STC_ST3215_COMMAND,
    body=cmd.encode(),
)
await send_commands(client, [driver_cmd])
```

## Files

- **`main.py`** - Auto-calibration workflow demonstrating full motor control sequence
- **`st3215.py`** - `St3215Driver` class wrapping the Python API
- **`arc.py`** - Position calculation utilities for handling encoder wraparound

## Running

```bash
# Single bus (auto-detects)
python main.py --server localhost

# Multiple buses (specify bus serial number)
python main.py --server localhost --bus-serial <bus-serial-number>
```

The script will:
1. Connect to station and subscribe to motor states
2. Find mechanical limits by moving motors until stall
3. Calculate and apply offset corrections
4. Test movement to normalized positions (0.0-1.0)

## Key Patterns

**State subscription:**
```python
self.inference_queue = asyncio.Queue()
self.error_queue = client.follow("st3215/inference", self.inference_queue)
entry = await self.inference_queue.get()
```

**Reading motor data:**
```python
state = st3215.InferenceStateReader(entry.Data)
for bus in state.get_buses():
    for motor in bus.get_motors():
        state_bytes = motor.get_state()
        position = get_position(state_bytes)
```

**Command tracking:**
```python
command_id = self.next_command_id()
await send_commands(self.client, [driver_cmd])
# Read states until command_id appears in motor's last_command field
```
