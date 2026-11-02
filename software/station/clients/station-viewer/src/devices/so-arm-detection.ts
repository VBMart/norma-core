import type { st3215 } from '@/api/proto.js';

/**
 * SO101 and SO102 leaders carry the same six STS3215s, but their base joints
 * differ a lot: SO101 turns 220 degrees, SO102 352 degrees. Once motor 1 has
 * a frozen calibration its swept range (in 0..4095 ticks, 4096 per turn)
 * tells the arms apart.
 */

const TICKS_PER_TURN = 4096;
const SO_ARM_BASE_MOTOR_ID = 1;

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

/** Which SO-ARM this bus is, or null while the base motor is not calibrated. */
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
