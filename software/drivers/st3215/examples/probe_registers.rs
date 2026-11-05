//! Read-only probe of the Feetech STS register layout, using the crate's own
//! packet code. Sends PING and READ only; never writes.
//!
//! Usage:
//!   cargo run -p st3215 --example probe_registers -- /dev/cu.usbmodemXXXX [id ...]
//!
//! With no ids it probes 1..=8. See docs/feetech-register-evidence.md for what
//! each byte is expected to contain.

use st3215::protocol::{ST3215Request, ST3215Response};
use tokio_serial::SerialPortBuilderExt;

const BAUD: u32 = 1_000_000;
const TIMEOUT_MS: u64 = 50;

fn model_name(n: u16) -> &'static str {
    match n {
        777 => "STS3215",
        2057 => "STS3235",
        2825 => "STS3250",
        521 => "STS3036",
        11272 => "SM8512BL",
        1284 => "SCS0009 (big-endian series)",
        _ => "unknown",
    }
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02X}")).collect::<Vec<_>>().join(" ")
}

async fn read<RW>(port: &mut RW, id: u8, address: u8, length: u8) -> Option<Vec<u8>>
where
    RW: tokio::io::AsyncRead + tokio::io::AsyncWrite + Unpin,
{
    let req = ST3215Request::Read { motor: id, address, length };
    match req.async_readwrite(port, TIMEOUT_MS).await {
        Ok(ST3215Response::Read { data, .. }) => Some(data.to_vec()),
        Ok(other) => {
            println!("  unexpected response to READ 0x{address:02X}: {other:?}");
            None
        }
        Err(e) => {
            println!("  READ 0x{address:02X} len {length} failed: {e:?}");
            None
        }
    }
}

#[tokio::main]
async fn main() {
    let mut args = std::env::args().skip(1);
    let Some(port_name) = args.next() else {
        eprintln!("usage: probe_registers <serial-port> [motor-id ...]");
        std::process::exit(2);
    };
    let ids: Vec<u8> = {
        let v: Vec<u8> = args.filter_map(|a| a.parse().ok()).collect();
        if v.is_empty() { (1..=8).collect() } else { v }
    };

    let mut port = tokio_serial::new(&port_name, BAUD)
        .open_native_async()
        .unwrap_or_else(|e| {
            eprintln!("cannot open {port_name}: {e}");
            std::process::exit(1);
        });
    println!("port {port_name} @ {BAUD} baud, probing ids {ids:?}\n");

    for id in ids {
        let ping = ST3215Request::Ping { motor: id };
        match ping.async_readwrite(&mut port, TIMEOUT_MS).await {
            Ok(_) => println!("id {id}: PING ok"),
            Err(_) => {
                println!("id {id}: no answer");
                continue;
            }
        }

        // 0x00..0x04: fw major, fw minor, END, model lo, model hi
        if let Some(v) = read(&mut port, id, 0x00, 5).await {
            let model = u16::from_le_bytes([v[3], v[4]]);
            println!(
                "  0x00..0x04 = [{}]  -> firmware {}.{}, END={}, model {} (0x{:04X}) = {}",
                hex(&v), v[0], v[1], v[2], model, model, model_name(model)
            );
        }

        // 0x03..0x04 on its own, the exact read the Feetech SDK ping() does
        if let Some(v) = read(&mut port, id, 0x03, 2).await {
            let model = u16::from_le_bytes([v[0], v[1]]);
            println!("  0x03..0x04 = [{}]  -> model {} = {}", hex(&v), model, model_name(model));
        }

        // 0x12 Phase, 0x13 Unload condition (default 44), 0x14 LED alarm (default 47)
        if let Some(v) = read(&mut port, id, 0x12, 3).await {
            let brushed = v[0] & 0b10 != 0;
            println!(
                "  0x12..0x14 = [{}]  -> phase=0b{:08b} (bit1 {}), unload={} (factory 44), led={} (factory 47)",
                hex(&v), v[0], if brushed { "brushed" } else { "brushless" }, v[1], v[2]
            );
        }

        // 0x18 min startup force (1 B), 0x19 integral limit (1 B)
        if let Some(v) = read(&mut port, id, 0x18, 2).await {
            println!("  0x18..0x19 = [{}]  -> min_startup_force={}, integral_limit={}", hex(&v), v[0], v[1]);
        }

        // 0x1C protection current, 6.5 mA/LSB
        if let Some(v) = read(&mut port, id, 0x1C, 2).await {
            let raw = u16::from_le_bytes([v[0], v[1]]);
            println!("  0x1C..0x1D = [{}]  -> protection_current={} (~{} mA)", hex(&v), raw, raw as u32 * 65 / 10);
        }
        println!();
    }
}
