//! Proves the firmware's streaming mode: sends STREAM_START, then reads
//! pushed frames for 10 seconds, reporting the received frame rate, CRC
//! failures, and firmware-tick freshness deltas.
//! cargo run -p arduino-nicla-sense-me --example stream_bench
use std::collections::BTreeMap;
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio_serial::SerialPortBuilderExt;

const CMD_STREAM_START: u8 = 0x02;
const CMD_STREAM_STOP: u8 = 0x03;
const MAGIC: [u8; 2] = [0xA5, 0x5A];
const PAYLOAD_LEN: usize = 0xA8;
const SAMPLE_COUNTER_REGISTER: usize = 0x01;
const RUN_SECONDS: u64 = 10;
const KEEPALIVE_EVERY: Duration = Duration::from_secs(1);

fn crc8(data: &[u8]) -> u8 {
    let mut crc: u8 = 0;
    for &byte in data {
        crc ^= byte;
        for _ in 0..8 {
            crc = if crc & 0x80 != 0 { (crc << 1) ^ 0x07 } else { crc << 1 };
        }
    }
    crc
}

#[tokio::main]
async fn main() -> Result<(), String> {
    let port = arduino_nicla_sense_me::find_usb_port()
        .ok_or("no Nicla Sense ME USB device found (vid 2341 pid 0060)")?;
    let mut stream = tokio_serial::new(&port, arduino_nicla_sense_me::SERIAL_BAUD)
        .timeout(Duration::from_millis(500))
        .open_native_async()
        .map_err(|error| format!("failed to open {port}: {error}"))?;
    arduino_nicla_sense_me::prepare_port(&mut stream)?;
    println!("port: {port}, streaming for {RUN_SECONDS}s...");

    stream
        .write_all(&[CMD_STREAM_START])
        .await
        .map_err(|error| format!("failed to start stream: {error}"))?;

    let deadline = tokio::time::Instant::now() + Duration::from_secs(RUN_SECONDS);
    let mut next_keepalive = tokio::time::Instant::now() + KEEPALIVE_EVERY;
    let mut frames = 0usize;
    let mut crc_failures = 0usize;
    let mut resyncs = 0usize;
    let mut counters: Vec<u8> = Vec::new();
    let started = tokio::time::Instant::now();

    'run: while tokio::time::Instant::now() < deadline {
        if tokio::time::Instant::now() >= next_keepalive {
            stream
                .write_all(&[CMD_STREAM_START])
                .await
                .map_err(|error| format!("keepalive failed: {error}"))?;
            next_keepalive += KEEPALIVE_EVERY;
        }

        // Scan to the frame magic (tolerates joining mid-stream).
        let mut byte = [0u8; 1];
        loop {
            match tokio::time::timeout(Duration::from_millis(500), stream.read_exact(&mut byte))
                .await
            {
                Ok(Ok(_)) => {}
                Ok(Err(error)) => return Err(format!("read error: {error}")),
                Err(_) => {
                    println!("timed out waiting for stream data");
                    break 'run;
                }
            }
            if byte[0] != MAGIC[0] {
                resyncs += 1;
                continue;
            }
            tokio::time::timeout(Duration::from_millis(500), stream.read_exact(&mut byte))
                .await
                .map_err(|_| "timeout mid-frame".to_string())?
                .map_err(|error| format!("read error: {error}"))?;
            if byte[0] == MAGIC[1] {
                break;
            }
            resyncs += 1;
        }

        let mut rest = [0u8; 1 + PAYLOAD_LEN + 1];
        tokio::time::timeout(Duration::from_millis(500), stream.read_exact(&mut rest))
            .await
            .map_err(|_| "timeout mid-frame".to_string())?
            .map_err(|error| format!("read error: {error}"))?;
        if rest[0] as usize != PAYLOAD_LEN {
            resyncs += 1;
            continue;
        }
        let payload = &rest[1..1 + PAYLOAD_LEN];
        if crc8(payload) != rest[1 + PAYLOAD_LEN] {
            crc_failures += 1;
            continue;
        }
        frames += 1;
        counters.push(payload[SAMPLE_COUNTER_REGISTER]);
    }
    let elapsed = started.elapsed();

    let _ = stream.write_all(&[CMD_STREAM_STOP]).await;

    println!(
        "received {frames} frames in {elapsed:?} -> {:.1} Hz  (crc failures: {crc_failures}, resync bytes: {resyncs})",
        frames as f64 / elapsed.as_secs_f64()
    );
    let mut deltas = BTreeMap::new();
    for pair in counters.windows(2) {
        *deltas.entry(pair[1].wrapping_sub(pair[0])).or_insert(0usize) += 1;
    }
    let histogram = deltas
        .iter()
        .map(|(delta, count)| format!("{delta} ticks x{count}"))
        .collect::<Vec<_>>()
        .join(", ");
    println!("firmware-tick deltas between frames: {histogram}");
    Ok(())
}
