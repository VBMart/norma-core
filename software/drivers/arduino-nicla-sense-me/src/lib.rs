pub mod arduino_nicla_sense_me_proto {
    include!("proto/arduino_nicla_sense_me.rs");
}

mod driver;

pub use driver::{
    ArduinoNiclaSenseMeBoardConfig, ArduinoNiclaSenseMeDriver, ArduinoNiclaSenseMeDriverConfig,
    ArduinoNiclaSenseMeTransport, DEFAULT_I2C_ADDRESS, FrameScanner, RAW_REGISTER_LENGTH,
    RAW_REGISTER_START, RX_QUEUE_ID, SERIAL_BAUD, SERIAL_CMD_STREAM_START, SERIAL_CMD_STREAM_STOP,
    USB_PID, USB_VID, find_usb_port, list_usb_ports, prepare_port, read_dump, read_frame,
    start_arduino_nicla_sense_me_driver,
};
