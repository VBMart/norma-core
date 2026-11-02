import { describe, expect, it } from 'vitest';
import type { st3215 } from '@/api/proto.js';
import {
  detectSt3215Model,
  listSt3215Models,
  resolveSt3215Kinematics,
  resolveSt3215Model,
  supportsSt3215Bus,
} from './st3215-models';

function makeBus(motorCount: number): st3215.InferenceState.IBusState {
  return {
    bus: { serialNumber: 'TEST' },
    motors: Array.from({ length: motorCount }, (_, index) => ({ id: index + 1 })),
  };
}

describe('ST3215 model catalog', () => {
  it('lists both six-motor arms for a six-motor bus, SO101 first', () => {
    expect(listSt3215Models(makeBus(6)).map((model) => model.id)).toEqual(['so101', 'so102']);
  });

  it('defaults a six-motor bus to SO101 when nothing is selected', () => {
    expect(resolveSt3215Model(makeBus(6))?.id).toBe('so101');
    expect(resolveSt3215Model(makeBus(6), null)?.id).toBe('so101');
  });

  it('honours a selected model that matches the bus', () => {
    expect(resolveSt3215Model(makeBus(6), 'so102')?.id).toBe('so102');
  });

  it('falls back to the default when the selected model does not fit the bus', () => {
    expect(resolveSt3215Model(makeBus(6), 'elrobot')?.id).toBe('so101');
    expect(resolveSt3215Model(makeBus(6), 'unknown')?.id).toBe('so101');
  });

  it('still resolves the eight-motor arm without a selection', () => {
    expect(resolveSt3215Model(makeBus(8))?.id).toBe('elrobot');
    expect(listSt3215Models(makeBus(8)).map((model) => model.id)).toEqual(['elrobot']);
  });

  it('rejects motor counts with no registered model', () => {
    expect(resolveSt3215Model(makeBus(5))).toBeNull();
    expect(listSt3215Models(makeBus(5))).toEqual([]);
    expect(supportsSt3215Bus(makeBus(5))).toBe(false);
    expect(supportsSt3215Bus(makeBus(6))).toBe(true);
  });

  it('resolves kinematics by joint count with the same default and override rules', () => {
    expect(resolveSt3215Kinematics(6)?.urdfPath).toContain('so101');
    expect(resolveSt3215Kinematics(6, 'so102')?.urdfPath).toContain('so102');
    expect(resolveSt3215Kinematics(8)?.urdfPath).toContain('elrobot');
    expect(resolveSt3215Kinematics(7)).toBeNull();
  });
});

describe('SO-ARM detection from the base motor calibration', () => {
  function makeSoArmBus(
    base: { rangeMin: number; rangeMax: number; rangeFreezed?: boolean },
  ): st3215.InferenceState.IBusState {
    const bus = makeBus(6);
    bus.motors![0] = { id: 1, rangeFreezed: true, ...base };
    return bus;
  }

  it('is undecided before calibration is frozen', () => {
    expect(detectSt3215Model(makeBus(6))).toBeNull();
    expect(detectSt3215Model(makeSoArmBus({ rangeMin: 50, rangeMax: 4050, rangeFreezed: false }))).toBeNull();
    expect(resolveSt3215Model(makeSoArmBus({ rangeMin: 50, rangeMax: 4050, rangeFreezed: false }), 'so101')?.id).toBe('so101');
  });

  it('is undecided when the base range is collapsed or too narrow', () => {
    expect(detectSt3215Model(makeSoArmBus({ rangeMin: 2000, rangeMax: 2000 }))).toBeNull();
    expect(detectSt3215Model(makeSoArmBus({ rangeMin: 2000, rangeMax: 2050 }))).toBeNull();
  });

  it('identifies SO101 from a ~220 degree base sweep, whatever was selected', () => {
    const bus = makeSoArmBus({ rangeMin: 800, rangeMax: 3300 });
    expect(detectSt3215Model(bus)?.id).toBe('so101');
    expect(resolveSt3215Model(bus, 'so102')?.id).toBe('so101');
  });

  it('identifies SO102 from a ~352 degree base sweep, whatever was selected', () => {
    const bus = makeSoArmBus({ rangeMin: 50, rangeMax: 4050 });
    expect(detectSt3215Model(bus)?.id).toBe('so102');
    expect(resolveSt3215Model(bus, 'so101')?.id).toBe('so102');
    expect(resolveSt3215Model(bus)?.id).toBe('so102');
  });

  it('measures a range that wraps past 4095 correctly', () => {
    // 3000 -> 4095 -> 0 -> 2900 is 3996 ticks, an SO102 sweep.
    expect(detectSt3215Model(makeSoArmBus({ rangeMin: 3000, rangeMax: 2900 }))?.id).toBe('so102');
    // 3500 -> 4095 -> 0 -> 1900 is 2496 ticks, an SO101 sweep.
    expect(detectSt3215Model(makeSoArmBus({ rangeMin: 3500, rangeMax: 1900 }))?.id).toBe('so101');
  });

  it('never detects an arm on buses with other motor counts', () => {
    const bus = makeBus(8);
    bus.motors![0] = { id: 1, rangeMin: 50, rangeMax: 4050, rangeFreezed: true };
    expect(detectSt3215Model(bus)).toBeNull();
    expect(resolveSt3215Model(bus)?.id).toBe('elrobot');
  });
});
