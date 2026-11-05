/// ST3215 motor settings presets

// ============================================================================
// Default Motor Settings
// ============================================================================

/// Default max torque
pub const DEFAULT_MAX_TORQUE: u16 = 500;

/// Default protection current
pub const DEFAULT_PROTECTION_CURRENT: u16 = 500; // 260;

/// Default overload torque
pub const DEFAULT_OVERLOAD_TORQUE: u8 = 25;

/// Default acceleration
pub const DEFAULT_ACCEL: u8 = 254;

/// Default torque limit
pub const DEFAULT_TORQUE_LIMIT: u16 = 500;

// ============================================================================
// Torque limits by servo model
// ============================================================================

/// Feetech model numbers (memory table address 0x03, little-endian).
pub const MODEL_STS3215: u16 = 777;
pub const MODEL_STS3235: u16 = 2057;
pub const MODEL_STS3250: u16 = 2825;

/// Torque and protection registers written on freeze and after calibration.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TorquePreset {
    /// EEPROM 0x10, 0..1000 = 0..100 % of stall torque; copied into 0x30 at power-up.
    pub max_torque: u16,
    /// RAM 0x30, same unit as `max_torque`.
    pub torque_limit: u16,
    /// EEPROM 0x1C, units of 6.5 mA, 0..511.
    pub protection_current: u16,
    /// EEPROM 0x24, % of max torque at which the overload timer starts (factory 80).
    pub overload_torque: u8,
}

/// Conservative preset for STS3215: half torque, overload protection from 25 % load.
pub const STS3215_TORQUE: TorquePreset = TorquePreset {
    max_torque: DEFAULT_MAX_TORQUE,
    torque_limit: DEFAULT_TORQUE_LIMIT,
    protection_current: DEFAULT_PROTECTION_CURRENT,
    overload_torque: DEFAULT_OVERLOAD_TORQUE,
};

/// Full torque for the larger STS3235 / STS3250 joint servos (SO-ARM102 follower).
/// Protection current stays at the register maximum (3.25 A), below the STS3250 stall current.
pub const HIGH_TORQUE: TorquePreset = TorquePreset {
    max_torque: 1000,
    torque_limit: 1000,
    protection_current: DEFAULT_PROTECTION_CURRENT,
    overload_torque: 80,
};

/// Torque preset by Feetech model number. Unknown or unreadable models get the STS3215 preset.
pub fn torque_preset_for_model(model: Option<u16>) -> TorquePreset {
    match model {
        Some(MODEL_STS3235) | Some(MODEL_STS3250) => HIGH_TORQUE,
        _ => STS3215_TORQUE,
    }
}

/// Motor count of the 8-motor ElRobot arm and the id of its gripper servo.
pub const ELROBOT_MOTOR_COUNT: u8 = 8;
pub const ELROBOT_GRIPPER_ID: u8 = 8;

/// Torque preset for one servo of a robot with `robot_motor_count` motors.
///
/// Large servos (STS3235/STS3250) always get full torque. On the 8-motor ElRobot every
/// joint servo runs at full torque as well, because its STS3215s are the only thing lifting
/// the arm; only the gripper keeps the conservative preset, since it stalls on objects by
/// design (LeRobot applies the same 50 % / 25 % values to its gripper).
pub fn torque_preset_for_motor(model: Option<u16>, robot_motor_count: u8, motor_id: u8) -> TorquePreset {
    let by_model = torque_preset_for_model(model);
    if by_model == HIGH_TORQUE {
        return HIGH_TORQUE;
    }
    if robot_motor_count == ELROBOT_MOTOR_COUNT && motor_id != ELROBOT_GRIPPER_ID {
        return HIGH_TORQUE;
    }
    STS3215_TORQUE
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn large_servos_get_full_torque() {
        assert_eq!(torque_preset_for_model(Some(MODEL_STS3250)), HIGH_TORQUE);
        assert_eq!(torque_preset_for_model(Some(MODEL_STS3235)), HIGH_TORQUE);
        assert_eq!(HIGH_TORQUE.max_torque, 1000);
        assert_eq!(HIGH_TORQUE.overload_torque, 80);
    }

    #[test]
    fn elrobot_joints_get_full_torque_but_not_the_gripper() {
        for id in 1..=7 {
            assert_eq!(torque_preset_for_motor(Some(MODEL_STS3215), ELROBOT_MOTOR_COUNT, id), HIGH_TORQUE);
        }
        assert_eq!(torque_preset_for_motor(Some(MODEL_STS3215), ELROBOT_MOTOR_COUNT, ELROBOT_GRIPPER_ID), STS3215_TORQUE);
        // A 6-motor SO arm keeps its STS3215 joints conservative and still lifts large servos.
        assert_eq!(torque_preset_for_motor(Some(MODEL_STS3215), 6, 2), STS3215_TORQUE);
        assert_eq!(torque_preset_for_motor(Some(MODEL_STS3250), 6, 2), HIGH_TORQUE);
        // Unknown motor count: model decides.
        assert_eq!(torque_preset_for_motor(None, 0, 2), STS3215_TORQUE);
    }

    #[test]
    fn sts3215_and_unknown_models_stay_conservative() {
        assert_eq!(torque_preset_for_model(Some(MODEL_STS3215)), STS3215_TORQUE);
        assert_eq!(torque_preset_for_model(Some(0)), STS3215_TORQUE);
        assert_eq!(torque_preset_for_model(None), STS3215_TORQUE);
        assert_eq!(STS3215_TORQUE.max_torque, DEFAULT_MAX_TORQUE);
    }
}

/// PID configuration for a motor bus
#[derive(Clone, Copy, Debug)]
pub struct PidConfig {
    pub p: u8,
    pub i: u8,
    pub d: u8,
}

/// PID config for ElRobot (8-motor arm)
pub const ELROBOT_PID: PidConfig = PidConfig { p: 16, i: 0, d: 0 };

/// PID config for SO101 (6-motor arm)
pub const SO101_PID: PidConfig = PidConfig { p: 16, i: 8, d: 32 };

/// Returns the appropriate PID config based on motor count
pub fn pid_config_for_motor_count(max_motors_cnt: u8) -> PidConfig {
    match max_motors_cnt {
        6 => SO101_PID,
        8 => ELROBOT_PID,
        _ => ELROBOT_PID, // default fallback
    }
}

// ============================================================================
// Calibration Motor Settings
// ============================================================================

/// Sweep speed during calibration
pub const CALIBRATION_SPEED: u16 = 365;

/// Sweep acceleration during calibration
pub const CALIBRATION_ACCEL: u8 = 50;

/// Torque limit during calibration
pub const CALIBRATION_TORQUE_LIMIT: u16 = 300;
