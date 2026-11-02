import { describe, expect, it } from 'vitest';
import type { st3215 } from '@/api/proto.js';
import {
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
