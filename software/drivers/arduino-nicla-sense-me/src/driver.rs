use crate::arduino_nicla_sense_me_proto::{
    ArduinoNiclaSenseMeDevice, ArduinoNiclaSenseMeDeviceInfo, ArduinoNiclaSenseMeSignalType,
    RxEnvelope,
};
use bytes::Bytes;
use i2c_async::AsyncI2cDevice;
use log::{debug, error, info, warn};
use normfs::{NormFS, QueueId, UintN};
use prost::Message;
use station_iface::StationEngine;
use station_iface::iface_proto::drivers::QueueDataType;
use std::collections::BTreeMap;
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::task::JoinHandle;
use tokio_serial::{SerialPort, SerialPortBuilderExt, SerialStream};

pub const RX_QUEUE_ID: &str = "arduino-nicla-sense-me/rx";
pub const DEFAULT_I2C_ADDRESS: u16 = 0x22;
pub const RAW_REGISTER_START: u8 = 0x00;
pub const RAW_REGISTER_LENGTH: usize = 0xA8;

const SOFTWARE_REVISION_REGISTER: usize = 0x0C;
const PRODUCT_ID_REGISTER: usize = 0x0D;
const SERIAL_NUMBER_REGISTER: usize = 0x0E;
const SERIAL_NUMBER_LENGTH: usize = 6;

pub const USB_VID: u16 = 0x2341;
pub const USB_PID: u16 = 0x0060;
const SERIAL_CMD_DUMP: u8 = 0x01;
const SERIAL_MAGIC: [u8; 2] = [0xA5, 0x5A];
const SERIAL_FRAME_LEN: usize = 3 + RAW_REGISTER_LENGTH + 1;
/// Real UART baud of the SAMD11 usb-bridge link; must match the firmware's
/// Serial.begin. 115200 capped polling at ~50 Hz (~15 ms per 172-byte dump).
pub const SERIAL_BAUD: u32 = 921_600;
const SERIAL_RESPONSE_TIMEOUT: Duration = Duration::from_millis(500);
/// While no board is attached, re-enumerate serial ports at most this often.
/// Enumeration walks the OS device tree (sysfs/IOKit) and is far too costly
/// to run on every 10 ms poll tick.
const USB_DISCOVER_BACKOFF: Duration = Duration::from_millis(500);
const PRODUCT_ID: u8 = 0x4D;

type DriverResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

#[derive(Debug, Clone)]
pub struct ArduinoNiclaSenseMeDriverConfig {
    pub poll_interval: Duration,
    pub boards: Vec<ArduinoNiclaSenseMeBoardConfig>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ArduinoNiclaSenseMeTransport {
    I2c {
        i2c_bus: u32,
    },
    Usb {
        /// Pin this board to a specific serial port (e.g. "/dev/ttyACM0").
        /// None autodetects by USB vid/pid — fine for a single board, but
        /// every additional USB board needs a distinct pinned port.
        usb_port: Option<String>,
    },
}

#[derive(Debug, Clone)]
pub struct ArduinoNiclaSenseMeBoardConfig {
    pub id: Option<String>,
    pub transport: ArduinoNiclaSenseMeTransport,
    /// Per-board override of the driver-wide poll interval.
    pub poll_interval: Option<Duration>,
}

impl Default for ArduinoNiclaSenseMeDriverConfig {
    fn default() -> Self {
        Self {
            poll_interval: Duration::from_secs(1),
            boards: Vec::new(),
        }
    }
}

pub struct ArduinoNiclaSenseMeDriver {
    _tasks: Vec<JoinHandle<()>>,
}

#[derive(Debug, Clone)]
struct Board {
    id: String,
    transport: ArduinoNiclaSenseMeTransport,
    poll_interval: Option<Duration>,
}

impl Board {
    fn key(transport: &ArduinoNiclaSenseMeTransport) -> String {
        match transport {
            ArduinoNiclaSenseMeTransport::I2c { i2c_bus } => format!("i2c-{i2c_bus}"),
            ArduinoNiclaSenseMeTransport::Usb {
                usb_port: Some(port),
            } => format!("usb-{port}"),
            ArduinoNiclaSenseMeTransport::Usb { usb_port: None } => "usb".to_string(),
        }
    }

    fn from_config(config: &ArduinoNiclaSenseMeBoardConfig) -> Self {
        Self {
            id: config
                .id
                .clone()
                .filter(|id| !id.trim().is_empty())
                .unwrap_or_else(|| Self::key(&config.transport)),
            transport: config.transport.clone(),
            poll_interval: config.poll_interval,
        }
    }

    fn proto(&self, data: Option<&[u8]>, usb_port: Option<&str>) -> ArduinoNiclaSenseMeDevice {
        let (i2c_bus, i2c_address, transport) = match &self.transport {
            ArduinoNiclaSenseMeTransport::I2c { i2c_bus } => {
                (*i2c_bus, DEFAULT_I2C_ADDRESS as u32, "i2c")
            }
            ArduinoNiclaSenseMeTransport::Usb { .. } => (0, 0, "usb"),
        };
        ArduinoNiclaSenseMeDevice {
            id: self.id.clone(),
            i2c_bus,
            i2c_address,
            transport: transport.to_string(),
            usb_port: usb_port.unwrap_or_default().to_string(),
            info: data.and_then(parse_device_info),
        }
    }
}

/// Builds the board set keyed by transport. The first board wins a key
/// collision; later duplicates are rejected loudly, since silently swapping
/// which physical board a configured id maps to would misattribute data.
fn build_boards(configs: &[ArduinoNiclaSenseMeBoardConfig]) -> BTreeMap<String, Board> {
    let mut boards = BTreeMap::new();
    for config in configs {
        let key = Board::key(&config.transport);
        if boards.contains_key(&key) {
            error!(
                "Arduino Nicla Sense ME board {:?} duplicates transport key {key} \
                 (give each USB board a distinct usb-port); skipping it",
                config.id
            );
            continue;
        }
        boards.insert(key, Board::from_config(config));
    }
    boards
}

/// Resolves a board's poll interval against the driver-wide fallback,
/// rejecting zero (tokio's `interval`-style pacing needs a non-zero period,
/// and a zero interval would busy-loop the worker).
fn effective_poll_interval(
    board_interval: Option<Duration>,
    fallback: Duration,
    board_id: &str,
) -> Duration {
    match board_interval {
        Some(value) if value == Duration::ZERO => {
            warn!(
                "Arduino Nicla Sense ME board {board_id} has a zero poll interval, \
                 using the driver-wide {fallback:?}"
            );
            fallback
        }
        Some(value) => value,
        None => fallback,
    }
}

impl ArduinoNiclaSenseMeDriver {
    pub async fn new<T: StationEngine>(
        normfs: Arc<NormFS>,
        station_engine: Arc<T>,
        config: ArduinoNiclaSenseMeDriverConfig,
    ) -> DriverResult<Self> {
        let rx_queue_id = normfs.resolve(RX_QUEUE_ID);
        normfs.ensure_queue_exists_for_write(&rx_queue_id).await?;
        station_engine.register_queue(
            &rx_queue_id,
            QueueDataType::QdtArduinoNiclaSenseMeRx,
            vec![],
        );

        let poll_interval = if config.poll_interval == Duration::ZERO {
            warn!("Arduino Nicla Sense ME poll interval is zero, using 1s");
            Duration::from_secs(1)
        } else {
            config.poll_interval
        };

        let boards = build_boards(&config.boards);
        if boards.is_empty() {
            warn!("Arduino Nicla Sense ME driver enabled with no boards configured");
        }

        let tasks = boards
            .values()
            .map(|board| {
                let board = board.clone();
                let normfs = normfs.clone();
                let rx_queue_id = rx_queue_id.clone();
                let interval =
                    effective_poll_interval(board.poll_interval, poll_interval, &board.id);
                let link = match &board.transport {
                    ArduinoNiclaSenseMeTransport::I2c { i2c_bus } => BoardLink::I2c(I2cLink {
                        device: AsyncI2cDevice::new(*i2c_bus, DEFAULT_I2C_ADDRESS),
                    }),
                    ArduinoNiclaSenseMeTransport::Usb { usb_port } => {
                        BoardLink::Usb(UsbLink::new(usb_port.clone()))
                    }
                };
                tokio::spawn(run_board_worker(normfs, rx_queue_id, board, interval, link))
            })
            .collect::<Vec<_>>();

        info!(
            "Started Arduino Nicla Sense ME driver for {} board(s)",
            boards.len()
        );

        Ok(Self { _tasks: tasks })
    }
}

pub async fn start_arduino_nicla_sense_me_driver<T: StationEngine>(
    normfs: Arc<NormFS>,
    station_engine: Arc<T>,
    config: ArduinoNiclaSenseMeDriverConfig,
) -> DriverResult<Arc<ArduinoNiclaSenseMeDriver>> {
    let driver = ArduinoNiclaSenseMeDriver::new(normfs, station_engine, config).await?;
    Ok(Arc::new(driver))
}

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

fn parse_dump_frame(frame: &[u8]) -> Result<Bytes, String> {
    if frame.len() != SERIAL_FRAME_LEN {
        return Err(format!("unexpected frame length {}", frame.len()));
    }
    if frame[0..2] != SERIAL_MAGIC {
        return Err(format!("bad frame magic {:#04x} {:#04x}", frame[0], frame[1]));
    }
    if frame[2] as usize != RAW_REGISTER_LENGTH {
        return Err(format!("bad payload length {:#04x}", frame[2]));
    }
    let payload = &frame[3..3 + RAW_REGISTER_LENGTH];
    let expected = frame[3 + RAW_REGISTER_LENGTH];
    let computed = crc8(payload);
    if computed != expected {
        return Err(format!("crc mismatch: computed {computed:#04x}, frame has {expected:#04x}"));
    }
    Ok(Bytes::copy_from_slice(payload))
}

/// All serial ports whose USB ids match the Nicla's SAMD11 bridge.
pub fn list_usb_ports() -> Vec<String> {
    let Ok(ports) = tokio_serial::available_ports() else {
        return Vec::new();
    };
    ports
        .into_iter()
        .filter_map(|port| match &port.port_type {
            tokio_serial::SerialPortType::UsbPort(usb)
                if usb.vid == USB_VID && usb.pid == USB_PID =>
            {
                // On macOS both /dev/tty.* and /dev/cu.* enumerate for one
                // device; prefer the callout (cu) device for host-initiated
                // CDC traffic. (Deliberate divergence from vesc-trampa,
                // which prefers tty; validated against real hardware — if
                // the probe hangs on open, flip this filter.)
                #[cfg(target_os = "macos")]
                if port.port_name.starts_with("/dev/tty.") {
                    return None;
                }
                Some(port.port_name)
            }
            _ => None,
        })
        .collect()
}

pub fn find_usb_port() -> Option<String> {
    list_usb_ports().into_iter().next()
}

/// Prepares a freshly opened port: asserts DTR (the mbed-core USB CDC stack
/// treats the port as closed until the host raises DTR) and clears any stale
/// input. Run once per connection — per-request ioctls cost milliseconds on
/// macOS and cap the achievable poll rate.
pub fn prepare_port(port: &mut SerialStream) -> Result<(), String> {
    port.write_data_terminal_ready(true)
        .map_err(|error| format!("failed to assert DTR: {error}"))?;
    port.clear(tokio_serial::ClearBuffer::Input)
        .map_err(|error| format!("failed to clear input buffer: {error}"))?;
    Ok(())
}

/// How one dump exchange failed — the connection-handling consequences
/// differ per class (see `UsbLink::poll`).
enum DumpError {
    /// The request went out but no complete frame arrived in time; the
    /// reply may still land later.
    Timeout,
    /// A complete frame arrived but failed validation (magic/length/CRC).
    Parse(String),
    /// The port itself failed.
    Io(String),
}

async fn read_dump_classified(port: &mut SerialStream) -> Result<Bytes, DumpError> {
    port.write_all(&[SERIAL_CMD_DUMP])
        .await
        .map_err(|error| DumpError::Io(format!("failed to send dump command: {error}")))?;
    let mut frame = [0u8; SERIAL_FRAME_LEN];
    tokio::time::timeout(SERIAL_RESPONSE_TIMEOUT, port.read_exact(&mut frame))
        .await
        .map_err(|_| DumpError::Timeout)?
        .map_err(|error| DumpError::Io(format!("failed to read dump frame: {error}")))?;
    parse_dump_frame(&frame).map_err(DumpError::Parse)
}

pub async fn read_dump(port: &mut SerialStream) -> Result<Bytes, String> {
    match read_dump_classified(port).await {
        Ok(data) => Ok(data),
        Err(DumpError::Timeout) => Err("timed out waiting for dump frame".to_string()),
        Err(DumpError::Parse(message)) | Err(DumpError::Io(message)) => Err(message),
    }
}

struct I2cLink {
    device: AsyncI2cDevice,
}

impl I2cLink {
    async fn poll(&mut self) -> Result<Bytes, String> {
        self.device
            .read_smbus_i2c_block_registers(RAW_REGISTER_START, RAW_REGISTER_LENGTH)
            .await
    }
}

struct UsbLink {
    pinned_port: Option<String>,
    connection: Option<(SerialStream, String)>,
    verified: bool,
    /// Clear the OS input buffer before the next request. Set after a
    /// timeout or parse error, and when a reply backlog is detected, so a
    /// single desynced exchange (e.g. a reply landing just after its
    /// timeout) can never leave the stream permanently one frame behind.
    resync: bool,
    next_discover: Option<tokio::time::Instant>,
}

impl UsbLink {
    fn new(pinned_port: Option<String>) -> Self {
        Self {
            pinned_port,
            connection: None,
            verified: false,
            resync: false,
            next_discover: None,
        }
    }

    fn find_port(&self) -> Option<String> {
        let ports = list_usb_ports();
        match &self.pinned_port {
            Some(pinned) => ports.into_iter().find(|port| port == pinned),
            None => ports.into_iter().next(),
        }
    }

    fn no_device_error(&self) -> String {
        match &self.pinned_port {
            Some(pinned) => {
                format!("Nicla Sense ME USB device not found at {pinned} (vid 2341 pid 0060)")
            }
            None => "no Nicla Sense ME USB device found (vid 2341 pid 0060)".to_string(),
        }
    }

    fn disconnect(&mut self) {
        self.connection = None;
        self.verified = false;
        self.resync = false;
    }

    fn connect(&mut self) -> Result<(), String> {
        let now = tokio::time::Instant::now();
        if let Some(next_discover) = self.next_discover {
            if now < next_discover {
                return Err(self.no_device_error());
            }
        }
        self.next_discover = Some(now + USB_DISCOVER_BACKOFF);

        let name = self.find_port().ok_or_else(|| self.no_device_error())?;
        let mut stream = tokio_serial::new(&name, SERIAL_BAUD)
            .timeout(SERIAL_RESPONSE_TIMEOUT)
            .open_native_async()
            .map_err(|error| format!("failed to open {name}: {error}"))?;
        prepare_port(&mut stream).map_err(|error| format!("{name}: {error}"))?;
        debug!("Opened Arduino Nicla Sense ME USB port {name}");
        self.connection = Some((stream, name));
        self.verified = false;
        self.resync = false;
        Ok(())
    }

    async fn poll(&mut self) -> Result<(Bytes, String), String> {
        if self.connection.is_none() {
            self.connect()?;
        }

        let (outcome, name) = {
            let (stream, name) = self.connection.as_mut().expect("connection populated above");
            if self.resync {
                if let Err(clear_error) = stream.clear(tokio_serial::ClearBuffer::Input) {
                    let name = name.clone();
                    self.disconnect();
                    return Err(format!("{name}: failed to clear input buffer: {clear_error}"));
                }
                self.resync = false;
            }
            (read_dump_classified(stream).await, name.clone())
        };

        match outcome {
            Ok(data) => {
                if !self.verified {
                    let product_id = data.get(PRODUCT_ID_REGISTER).copied();
                    if product_id != Some(PRODUCT_ID) {
                        self.disconnect();
                        return Err(format!("{name}: unexpected product id {product_id:?}"));
                    }
                    self.verified = true;
                }
                // Leftover bytes after a complete frame mean this reply was
                // a stale one from an earlier request (each request produces
                // exactly one reply); resync before the next request so the
                // stream cannot stay a frame behind.
                if let Some((stream, _)) = self.connection.as_ref() {
                    if stream.bytes_to_read().unwrap_or(0) > 0 {
                        self.resync = true;
                    }
                }
                Ok((data, name))
            }
            Err(DumpError::Timeout) => {
                // The reply may still land after the deadline; drop it
                // before the next request instead of paying a full
                // reopen+DTR cycle for a transient hiccup.
                self.resync = true;
                Err(format!("{name}: timed out waiting for dump frame"))
            }
            Err(DumpError::Parse(message)) => {
                self.resync = true;
                Err(format!("{name}: {message}"))
            }
            Err(DumpError::Io(message)) => {
                self.disconnect();
                Err(format!("{name}: {message}"))
            }
        }
    }
}

/// One transport connection to a board: yields a register image (and the
/// serial port it came from, for USB) per poll. Connection management,
/// recovery, and backoff live inside the link; the worker only sees
/// `Ok(image)` / `Err(message)`.
enum BoardLink {
    I2c(I2cLink),
    Usb(UsbLink),
}

impl BoardLink {
    async fn poll(&mut self) -> Result<(Bytes, Option<String>), String> {
        match self {
            BoardLink::I2c(link) => link.poll().await.map(|data| (data, None)),
            BoardLink::Usb(link) => link.poll().await.map(|(data, port)| (data, Some(port))),
        }
    }
}

async fn run_board_worker(
    normfs: Arc<NormFS>,
    rx_queue_id: QueueId,
    board: Board,
    poll_interval: Duration,
    mut link: BoardLink,
) {
    let mut connected = false;
    let mut last_port = None::<String>;
    let mut last_data = None::<Bytes>;
    let mut last_error = None::<String>;
    // Min-interval pacing rather than a fixed-boundary interval: when the
    // poll round-trip exceeds the interval (USB bridge latency is ~15 ms),
    // the next poll starts immediately instead of being quantized up to the
    // next interval boundary (which would halve the achievable rate).
    let mut next_poll = tokio::time::Instant::now();

    loop {
        tokio::time::sleep_until(next_poll).await;
        next_poll = tokio::time::Instant::now() + poll_interval;

        match link.poll().await {
            Ok((data, port_name)) => {
                if !connected {
                    send_board_signal(
                        &normfs,
                        &rx_queue_id,
                        &board,
                        ArduinoNiclaSenseMeSignalType::ArduinoNiclaSenseMeConnected,
                        Some(&data),
                        None,
                        port_name.as_deref(),
                    );
                    connected = true;
                }
                send_board_signal(
                    &normfs,
                    &rx_queue_id,
                    &board,
                    ArduinoNiclaSenseMeSignalType::ArduinoNiclaSenseMeRegistersSnapshot,
                    Some(&data),
                    None,
                    port_name.as_deref(),
                );
                last_port = port_name;
                last_data = Some(data);
                last_error = None;
            }
            Err(poll_error) => {
                if connected {
                    send_board_signal(
                        &normfs,
                        &rx_queue_id,
                        &board,
                        ArduinoNiclaSenseMeSignalType::ArduinoNiclaSenseMeDisconnected,
                        last_data.as_ref(),
                        Some(poll_error.clone()),
                        last_port.as_deref(),
                    );
                    connected = false;
                }
                if last_error.as_deref() != Some(poll_error.as_str()) {
                    send_board_signal(
                        &normfs,
                        &rx_queue_id,
                        &board,
                        ArduinoNiclaSenseMeSignalType::ArduinoNiclaSenseMeError,
                        last_data.as_ref(),
                        Some(poll_error.clone()),
                        last_port.as_deref(),
                    );
                    last_error = Some(poll_error);
                }
            }
        }
    }
}

fn parse_device_info(data: &[u8]) -> Option<ArduinoNiclaSenseMeDeviceInfo> {
    let serial_end = SERIAL_NUMBER_REGISTER + SERIAL_NUMBER_LENGTH;
    if data.len() < serial_end {
        return None;
    }

    Some(ArduinoNiclaSenseMeDeviceInfo {
        software_revision: data[SOFTWARE_REVISION_REGISTER] as u32,
        product_id: data[PRODUCT_ID_REGISTER] as u32,
        serial_number: Bytes::copy_from_slice(&data[SERIAL_NUMBER_REGISTER..serial_end]),
    })
}

fn send_board_signal(
    normfs: &Arc<NormFS>,
    rx_queue_id: &QueueId,
    board: &Board,
    signal_type: ArduinoNiclaSenseMeSignalType,
    data: Option<&Bytes>,
    error_message: Option<String>,
    usb_port: Option<&str>,
) {
    let envelope = RxEnvelope {
        monotonic_stamp_ns: systime::get_monotonic_stamp_ns(),
        local_stamp_ns: systime::get_local_stamp_ns(),
        app_start_id: systime::get_app_start_id(),
        signal_type: signal_type as i32,
        device: Some(board.proto(data.map(|data| data.as_ref()), usb_port)),
        data: data.cloned().unwrap_or_default(),
        error: error_message.unwrap_or_default(),
    };

    if let Err(send_error) = send_proto(normfs, rx_queue_id, &envelope) {
        error!(
            "Failed to send Arduino Nicla Sense ME {:?} signal for {}: {}",
            signal_type, board.id, send_error
        );
    }
}

fn send_proto<M: Message>(
    normfs: &NormFS,
    queue_id: &QueueId,
    envelope: &M,
) -> DriverResult<UintN> {
    let mut buffer = Vec::new();
    envelope.encode(&mut buffer)?;
    Ok(normfs.enqueue(queue_id, Bytes::from(buffer))?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn board_id_defaults_to_transport_key() {
        let board = Board::from_config(&ArduinoNiclaSenseMeBoardConfig {
            id: None,
            transport: ArduinoNiclaSenseMeTransport::I2c { i2c_bus: 2 },
            poll_interval: None,
        });
        assert_eq!(board.id, "i2c-2");

        let board = Board::from_config(&ArduinoNiclaSenseMeBoardConfig {
            id: Some("  ".to_string()),
            transport: ArduinoNiclaSenseMeTransport::Usb { usb_port: None },
            poll_interval: None,
        });
        assert_eq!(board.id, "usb");

        let board = Board::from_config(&ArduinoNiclaSenseMeBoardConfig {
            id: None,
            transport: ArduinoNiclaSenseMeTransport::Usb {
                usb_port: Some("/dev/ttyACM1".to_string()),
            },
            poll_interval: None,
        });
        assert_eq!(board.id, "usb-/dev/ttyACM1");

        let board = Board::from_config(&ArduinoNiclaSenseMeBoardConfig {
            id: Some("imu-front".to_string()),
            transport: ArduinoNiclaSenseMeTransport::Usb { usb_port: None },
            poll_interval: None,
        });
        assert_eq!(board.id, "imu-front");
    }

    #[test]
    fn build_boards_keeps_first_on_duplicate_key() {
        let boards = build_boards(&[
            ArduinoNiclaSenseMeBoardConfig {
                id: Some("first".to_string()),
                transport: ArduinoNiclaSenseMeTransport::Usb { usb_port: None },
                poll_interval: None,
            },
            ArduinoNiclaSenseMeBoardConfig {
                id: Some("second".to_string()),
                transport: ArduinoNiclaSenseMeTransport::Usb { usb_port: None },
                poll_interval: None,
            },
        ]);
        assert_eq!(boards.len(), 1);
        assert_eq!(boards["usb"].id, "first");
    }

    #[test]
    fn build_boards_separates_pinned_usb_ports() {
        let boards = build_boards(&[
            ArduinoNiclaSenseMeBoardConfig {
                id: Some("front".to_string()),
                transport: ArduinoNiclaSenseMeTransport::Usb {
                    usb_port: Some("/dev/ttyACM0".to_string()),
                },
                poll_interval: None,
            },
            ArduinoNiclaSenseMeBoardConfig {
                id: Some("rear".to_string()),
                transport: ArduinoNiclaSenseMeTransport::Usb {
                    usb_port: Some("/dev/ttyACM1".to_string()),
                },
                poll_interval: None,
            },
        ]);
        assert_eq!(boards.len(), 2);
    }

    #[test]
    fn effective_poll_interval_rejects_zero() {
        let fallback = Duration::from_secs(1);
        assert_eq!(
            effective_poll_interval(Some(Duration::ZERO), fallback, "board"),
            fallback
        );
        assert_eq!(
            effective_poll_interval(Some(Duration::from_millis(10)), fallback, "board"),
            Duration::from_millis(10)
        );
        assert_eq!(effective_poll_interval(None, fallback, "board"), fallback);
    }

    #[test]
    fn parse_device_info_reads_header() {
        let mut data = vec![0u8; RAW_REGISTER_LENGTH];
        data[SOFTWARE_REVISION_REGISTER] = 1;
        data[PRODUCT_ID_REGISTER] = 0x4D;
        data[SERIAL_NUMBER_REGISTER..SERIAL_NUMBER_REGISTER + SERIAL_NUMBER_LENGTH]
            .copy_from_slice(&[0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]);

        let info = parse_device_info(&data).expect("info");
        assert_eq!(info.software_revision, 1);
        assert_eq!(info.product_id, 0x4D);
        assert_eq!(info.serial_number.as_ref(), &[0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]);
    }

    #[test]
    fn parse_device_info_rejects_short_buffer() {
        assert!(parse_device_info(&[0u8; 0x10]).is_none());
    }

    #[test]
    fn crc8_matches_check_value() {
        // Standard CRC-8 (poly 0x07, init 0x00) check value for "123456789".
        assert_eq!(crc8(b"123456789"), 0xF4);
        assert_eq!(crc8(&[]), 0x00);
    }

    fn build_frame(payload: &[u8]) -> Vec<u8> {
        let mut frame = vec![0xA5, 0x5A, payload.len() as u8];
        frame.extend_from_slice(payload);
        frame.push(crc8(payload));
        frame
    }

    #[test]
    fn parse_dump_frame_roundtrip() {
        let mut payload = vec![0u8; RAW_REGISTER_LENGTH];
        payload[0x0D] = 0x4D;
        let frame = build_frame(&payload);
        let parsed = parse_dump_frame(&frame).expect("valid frame parses");
        assert_eq!(parsed.as_ref(), payload.as_slice());
    }

    #[test]
    fn parse_dump_frame_rejects_corruption() {
        let payload = vec![0u8; RAW_REGISTER_LENGTH];
        let good = build_frame(&payload);

        let mut bad_magic = good.clone();
        bad_magic[0] = 0x00;
        assert!(parse_dump_frame(&bad_magic).is_err());

        let mut bad_len = good.clone();
        bad_len[2] = 0x10;
        assert!(parse_dump_frame(&bad_len).is_err());

        let mut bad_crc = good.clone();
        *bad_crc.last_mut().unwrap() ^= 0xFF;
        assert!(parse_dump_frame(&bad_crc).is_err());

        assert!(parse_dump_frame(&good[..good.len() - 1]).is_err());
    }
}
