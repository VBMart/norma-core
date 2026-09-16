//! Proves the firmware's streaming mode: sends STREAM_START, then reads
//! pushed frames for 10 seconds, reporting the received frame rate, the
//! frames the scanner discarded (corrupt or misaligned), and firmware-tick
//! freshness deltas.
//! cargo run -p arduino-nicla-sense-me --example stream_bench
use arduino_nicla_sense_me::{
    FrameScanner, SERIAL_BAUD, SERIAL_CMD_STREAM_START, SERIAL_CMD_STREAM_STOP, find_usb_port,
    prepare_port, read_frame,
};
use std::collections::BTreeMap;
use std::time::Duration;
use tokio::io::AsyncWriteExt;
use tokio_serial::SerialPortBuilderExt;

const SAMPLE_COUNTER_REGISTER: usize = 0x01;
const RUN_SECONDS: u64 = 10;
const KEEPALIVE_EVERY: Duration = Duration::from_secs(1);
const FRAME_TIMEOUT: Duration = Duration::from_millis(500);

#[tokio::main]
async fn main() -> Result<(), String> {
    let port = find_usb_port().ok_or("no Nicla Sense ME USB device found (vid 2341 pid 0060)")?;
    let mut stream = tokio_serial::new(&port, SERIAL_BAUD)
        .timeout(FRAME_TIMEOUT)
        .open_native_async()
        .map_err(|error| format!("failed to open {port}: {error}"))?;
    prepare_port(&mut stream).await?;
    println!("port: {port}, streaming for {RUN_SECONDS}s...");

    stream
        .write_all(&[SERIAL_CMD_STREAM_START])
        .await
        .map_err(|error| format!("failed to start stream: {error}"))?;

    let deadline = tokio::time::Instant::now() + Duration::from_secs(RUN_SECONDS);
    let mut next_keepalive = tokio::time::Instant::now() + KEEPALIVE_EVERY;
    let mut scanner = FrameScanner::default();
    let mut frames = 0usize;
    let mut counters: Vec<u8> = Vec::new();
    let started = tokio::time::Instant::now();

    while tokio::time::Instant::now() < deadline {
        if tokio::time::Instant::now() >= next_keepalive {
            stream
                .write_all(&[SERIAL_CMD_STREAM_START])
                .await
                .map_err(|error| format!("keepalive failed: {error}"))?;
            next_keepalive += KEEPALIVE_EVERY;
        }
        match read_frame(&mut stream, &mut scanner, FRAME_TIMEOUT).await {
            Ok(payload) => {
                frames += 1;
                counters.push(payload[SAMPLE_COUNTER_REGISTER]);
            }
            Err(error) => {
                println!("stream stalled: {error}");
                break;
            }
        }
    }
    let elapsed = started.elapsed();
    let discarded = scanner.take_bad_frames();

    let _ = stream.write_all(&[SERIAL_CMD_STREAM_STOP]).await;

    println!(
        "received {frames} frames in {elapsed:?} -> {:.1} Hz  (discarded frames: {discarded})",
        frames as f64 / elapsed.as_secs_f64()
    );
    let mut deltas = BTreeMap::new();
    for pair in counters.windows(2) {
        *deltas
            .entry(pair[1].wrapping_sub(pair[0]))
            .or_insert(0usize) += 1;
    }
    let histogram = deltas
        .iter()
        .map(|(delta, count)| format!("{delta} ticks x{count}"))
        .collect::<Vec<_>>()
        .join(", ");
    println!("firmware-tick deltas between frames: {histogram}");
    Ok(())
}
