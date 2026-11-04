import { describe, expect, it } from 'vitest';
import type { st3215 } from '@/api/proto.js';
import {
  FEETECH_MODEL,
  classifySoArm,
  classifySoArmBase,
  getMotorRangeSpan,
  isSo102FollowerBus,
} from './so-arm-detection';

const MEMORY_SNAPSHOT_LENGTH = 0x47;

function motorMemory(modelNumber: number): Uint8Array {
  const data = new Uint8Array(MEMORY_SNAPSHOT_LENGTH);
  data[3] = modelNumber & 0xff;
  data[4] = (modelNumber >> 8) & 0xff;
  return data;
}

function makeBus(models: number[], base?: Partial<st3215.InferenceState.IMotorState>): st3215.InferenceState.IBusState {
  return {
    bus: { serialNumber: 'TEST' },
    motors: models.map((model, index) => ({
      id: index + 1,
      state: motorMemory(model),
      ...(index === 0 ? base : {}),
    })),
  };
}

const { STS3215, STS3235, STS3250 } = FEETECH_MODEL;
const ALL_3215 = [STS3215, STS3215, STS3215, STS3215, STS3215, STS3215];
// Robonine's layout: STS3235 base and wrist flex, STS3250 shoulder and elbow.
const OFFICIAL_FOLLOWER = [STS3235, STS3250, STS3250, STS3235, STS3215, STS3215];
// A build with STS3250 only in the shoulder and elbow.
const MIXED_FOLLOWER = [STS3215, STS3250, STS3250, STS3215, STS3215, STS3215];

describe('SO102 follower detection from servo models', () => {
  it('recognises the official and the STS3250-only follower layouts', () => {
    expect(isSo102FollowerBus(makeBus(OFFICIAL_FOLLOWER))).toBe(true);
    expect(isSo102FollowerBus(makeBus(MIXED_FOLLOWER))).toBe(true);
    expect(classifySoArm(makeBus(MIXED_FOLLOWER))).toBe('so102');
  });

  it('treats six STS3215s as not a follower', () => {
    expect(isSo102FollowerBus(makeBus(ALL_3215))).toBe(false);
  });

  it('ignores buses that are not six motors with ids 1..6', () => {
    expect(isSo102FollowerBus(makeBus(OFFICIAL_FOLLOWER.slice(0, 5)))).toBe(false);
    const bus = makeBus(OFFICIAL_FOLLOWER);
    bus.motors![5] = { ...bus.motors![5], id: 7 };
    expect(isSo102FollowerBus(bus)).toBe(false);
  });

  it('needs a memory snapshot long enough to hold the model number', () => {
    const bus = makeBus(OFFICIAL_FOLLOWER);
    bus.motors = bus.motors!.map((motor) => ({ ...motor, state: new Uint8Array(3) }));
    expect(isSo102FollowerBus(bus)).toBe(false);
    bus.motors = bus.motors.map((motor) => ({ ...motor, state: undefined }));
    expect(isSo102FollowerBus(bus)).toBe(false);
  });
});

describe('SO-ARM classification', () => {
  it('lets the servo models win over a short base sweep', () => {
    const bus = makeBus(MIXED_FOLLOWER, { rangeMin: 1000, rangeMax: 3000, rangeFreezed: true });
    expect(classifySoArmBase(bus)).toBe('so101');
    expect(classifySoArm(bus)).toBe('so102');
  });

  it('falls back to the base sweep for six STS3215s', () => {
    expect(classifySoArm(makeBus(ALL_3215))).toBeNull();
    expect(classifySoArm(makeBus(ALL_3215, { rangeMin: 5, rangeMax: 4091, rangeFreezed: true }))).toBe('so102');
    expect(classifySoArm(makeBus(ALL_3215, { rangeMin: 800, rangeMax: 3300, rangeFreezed: true }))).toBe('so101');
  });

  it('measures a wrapped sweep along the arc', () => {
    expect(getMotorRangeSpan({ id: 1, rangeMin: 3500, rangeMax: 500 })).toBe(1096);
  });
});
