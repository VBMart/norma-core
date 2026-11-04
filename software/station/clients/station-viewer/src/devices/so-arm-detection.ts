import type { st3215 } from '@/api/proto.js';
import { getMotorModelNumber } from '@/st3215/motor-parser';

/**
 * Telling SO-ARMs apart from the bus.
 *
 * Followers: SO102 followers mix servo models (STS3235/STS3250 in the
 * shoulder and elbow, STS3215 elsewhere) while SO101 arms are six STS3215s,
 * so any STS3235/STS3250 on a six-motor bus is an SO102 follower. That works
 * before calibration.
 *
 * Leaders: both leaders carry six STS3215s, but their base joints differ a
 * lot (SO101 220 degrees, SO102 352 degrees). Once motor 1 has a frozen
 * calibration its swept range (in 0..4095 ticks, 4096 per turn) tells them
 * apart.
 */

const TICKS_PER_TURN = 4096;
const SO_ARM_MOTOR_COUNT = 6;
const SO_ARM_BASE_MOTOR_ID = 1;

/** Feetech model numbers (memory table address 3, little-endian). */
export const FEETECH_MODEL = {
  STS3215: 777,
  STS3235: 2057,
  STS3250: 2825,
} as const;

const SO102_FOLLOWER_MODELS: ReadonlySet<number> = new Set([FEETECH_MODEL.STS3235, FEETECH_MODEL.STS3250]);

/** SO101 base: 220 deg ~ 2500 ticks. SO102 base: 352 deg ~ 4005 ticks. */
export const SO_ARM_BASE_SPAN_THRESHOLD_TICKS = Math.round((270 / 360) * TICKS_PER_TURN);

/** Below this the calibration is not a real sweep (fresh/reset motors). */
const MIN_BASE_SPAN_TICKS = 100;

export type SoArmKind = 'so101' | 'so102';

/** Swept range in ticks, following the arc from rangeMin up to rangeMax even when it wraps past 4095. */
export function getMotorRangeSpan(motor: st3215.InferenceState.IMotorState): number {
  const min = motor.rangeMin ?? 0;
  const max = motor.rangeMax ?? 0;
  return max >= min ? max - min : TICKS_PER_TURN - min + max;
}

function isSoArmBus(bus: st3215.InferenceState.IBusState): boolean {
  const motors = bus.motors ?? [];
  return motors.length === SO_ARM_MOTOR_COUNT
    && motors.every((motor) => typeof motor.id === 'number' && motor.id >= 1 && motor.id <= SO_ARM_MOTOR_COUNT);
}

/** True when the bus carries an SO102 follower: six motors with an STS3235 or STS3250 among them. */
export function isSo102FollowerBus(bus: st3215.InferenceState.IBusState): boolean {
  if (!isSoArmBus(bus)) {
    return false;
  }
  return (bus.motors ?? []).some((motor) => {
    const model = motor.state ? getMotorModelNumber(motor.state) : null;
    return model !== null && SO102_FOLLOWER_MODELS.has(model);
  });
}

/** Which SO-ARM the base sweep says this is, or null while motor 1 is not calibrated. */
export function classifySoArmBase(bus: st3215.InferenceState.IBusState): SoArmKind | null {
  const base = bus.motors?.find((motor) => motor.id === SO_ARM_BASE_MOTOR_ID);
  if (!base || base.rangeFreezed !== true) {
    return null;
  }
  const span = getMotorRangeSpan(base);
  if (span < MIN_BASE_SPAN_TICKS) {
    return null;
  }
  return span >= SO_ARM_BASE_SPAN_THRESHOLD_TICKS ? 'so102' : 'so101';
}

/**
 * Which SO-ARM this bus is, or null when nothing identifies it yet. Servo
 * models are hardware evidence and win over the calibration sweep.
 */
export function classifySoArm(bus: st3215.InferenceState.IBusState): SoArmKind | null {
  if (isSo102FollowerBus(bus)) {
    return 'so102';
  }
  return classifySoArmBase(bus);
}
