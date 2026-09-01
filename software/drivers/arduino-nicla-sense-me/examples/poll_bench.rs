//! Measures the sustained USB dump rate: back-to-back polls with no pacing,
//! reporting round-trip latency percentiles, the achievable frame rate, and
//! how many firmware ticks (10 ms each, via the sample counter) pass between
//! consecutive frames.
//! cargo run -p arduino-nicla-sense-me --example poll_bench
use std::collections::BTreeMap;
use std::time::{Duration, Instant};
use tokio_serial::SerialPortBuilderExt;

const WARMUP: usize = 20;
const ITERATIONS: usize = 1000;
const SAMPLE_COUNTER_REGISTER: usize = 0x01;

#[tokio::main]
async fn main() -> Result<(), String> {
    let port = arduino_nicla_sense_me::find_usb_port()
        .ok_or("no Nicla Sense ME USB device found (vid 2341 pid 0060)")?;
    let mut stream = tokio_serial::new(&port, arduino_nicla_sense_me::SERIAL_BAUD)
        .timeout(Duration::from_millis(500))
        .open_native_async()
        .map_err(|error| format!("failed to open {port}: {error}"))?;
    arduino_nicla_sense_me::prepare_port(&mut stream)?;
    println!("port: {port}, {ITERATIONS} back-to-back dumps after {WARMUP} warmup polls");

    for _ in 0..WARMUP {
        arduino_nicla_sense_me::read_dump(&mut stream).await?;
    }

    let mut durations = Vec::with_capacity(ITERATIONS);
    let mut counters = Vec::with_capacity(ITERATIONS);
    let started = Instant::now();
    for _ in 0..ITERATIONS {
        let poll_started = Instant::now();
        let data = arduino_nicla_sense_me::read_dump(&mut stream).await?;
        durations.push(poll_started.elapsed());
        counters.push(data[SAMPLE_COUNTER_REGISTER]);
    }
    let total = started.elapsed();

    durations.sort();
    let percentile = |p: f64| durations[((durations.len() - 1) as f64 * p) as usize];
    let avg = total / ITERATIONS as u32;
    println!("round-trip:  min {:?}  p50 {:?}  p90 {:?}  p99 {:?}  max {:?}",
        durations[0], percentile(0.50), percentile(0.90), percentile(0.99),
        durations[durations.len() - 1]);
    println!("average:     {avg:?}/frame -> sustained {:.1} Hz (unpaced)",
        ITERATIONS as f64 / total.as_secs_f64());

    // Firmware tick deltas between consecutive frames (u8 counter, one tick
    // per 10 ms refresh): delta 0 = same snapshot twice (polling faster than
    // the firmware refreshes), 1 = every frame fresh, >1 = frames skipped.
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
