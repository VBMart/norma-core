# Station Go Client Library

Go client library for connecting to and interacting with Station servers.

> **Note:** This is the **Go** client library. Python and other language clients are planned.

## Overview

The `station` package provides a convenient client interface for connecting to Station servers, reading from queues, and sending commands to robots.

## Installation

```go
import "norma_core/software/station/shared/station"
```

## Quick Start

### Creating a Client

Use `NewStationClient` to connect to a Station server:

```go
client, err := station.NewStationClient("192.168.1.100")
if err != nil {
    return fmt.Errorf("failed to create station client: %w", err)
}
```

The function accepts:
- **IP address or hostname**: `"192.168.1.100"` or `"localhost"`
- **IP with port**: `"192.168.1.100:8888"`
- **Defaults to port 8888** if not specified

## Usage Examples

### Example: Reading from a Queue

See [dataset-generator](../../bin/dataset-generator/dataset-generator.go) for a complete example:

```go
// Connect to station
client, err := station.NewStationClient(robotAddress)
if err != nil {
    return fmt.Errorf("failed to create station client: %w", err)
}

// Read queue entries
frames, errChan := internal.StreamFrames(client, queueName, bounds)

for frame := range frames {
    // Process each frame
    processFrame(frame)
}

// Check for errors
if err := <-errChan; err != nil {
    return fmt.Errorf("failed to read range: %w", err)
}
```

### Example: Sending Commands

```go
import commandspb "norma_core/target/generated-sources/protobuf/station/commands"

// Create commands
commands := []*commandspb.DriverCommand{
    // ... your commands
}

// Send to robot
err := station.SendCommands(client, commands)
if err != nil {
    return fmt.Errorf("failed to send commands: %w", err)
}
```

## Complete Example

See the [dataset-generator](../../bin/dataset-generator) tool for a full working example that:
- Connects to a station
- Reads from the inference queue
- Processes frames and generates datasets
