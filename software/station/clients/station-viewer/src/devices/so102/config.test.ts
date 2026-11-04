import { describe, expect, it } from 'vitest';
import type { st3215 } from '@/api/proto.js';
import {
  resolveSo102IsLeader,
  resolveSo102JointNames,
  resolveSo102JointValue,
  resolveSo102MotorMaterialIndex,
  resolveSo102UrdfPath,
} from './config';

describe('SO102 config', () => {
  it('picks the URDF and joint names by role', () => {
    expect(resolveSo102UrdfPath(true)).toBe('devices/so102/so102_robot_leader.urdf');
    expect(resolveSo102UrdfPath(false)).toBe('devices/so102/so102_robot_follower.urdf');
    expect(resolveSo102JointNames(true)[5]).toEqual(['trigger']);
    expect(resolveSo102JointNames(false)[5]).toEqual(['clamp1']);
    expect(resolveSo102JointNames(true).slice(0, 5)).toEqual(resolveSo102JointNames(false).slice(0, 5));
  });

  it('maps motor 6 inverted: calibrated minimum is the open gripper / released trigger', () => {
    const clamp = { jointName: 'clamp1', lowerLimit: 0, upperLimit: 0.0415 };
    expect(resolveSo102JointValue({ ...clamp, position: 0 })).toBeCloseTo(0.0415);
    expect(resolveSo102JointValue({ ...clamp, position: 1 })).toBeCloseTo(0);
    expect(resolveSo102JointValue({ ...clamp, position: 0.25 })).toBeCloseTo(0.031125);
    const trigger = { jointName: 'trigger', lowerLimit: -0.6, upperLimit: 0 };
    expect(resolveSo102JointValue({ ...trigger, position: 0 })).toBeCloseTo(0);
    expect(resolveSo102JointValue({ ...trigger, position: 1 })).toBeCloseTo(-0.6);
  });

  it('maps motor materials to motor indices and ignores the frame', () => {
    expect(resolveSo102MotorMaterialIndex({ materialName: 'so102_motor_1_material', motorCount: 6 })).toBe(0);
    expect(resolveSo102MotorMaterialIndex({ materialName: 'so102_motor_6_material', motorCount: 6 })).toBe(5);
    expect(resolveSo102MotorMaterialIndex({ materialName: 'so102_motor_7_material', motorCount: 6 })).toBeNull();
    expect(resolveSo102MotorMaterialIndex({ materialName: 'silver', motorCount: 6 })).toBeNull();
  });
});

describe('SO102 role from the bus', () => {
  const snapshotWithModel = (model: number) => {
    const data = new Uint8Array(0x47);
    data[3] = model & 0xff;
    data[4] = model >> 8;
    return data;
  };
  const bus = (model: number): st3215.InferenceState.IBusState => ({
    bus: { serialNumber: 'TEST' },
    motors: Array.from({ length: 6 }, (_, index) => ({ id: index + 1, state: snapshotWithModel(index === 1 ? model : 777) })),
  });

  it('renders the follower when the bus carries an STS3250', () => {
    expect(resolveSo102IsLeader(bus(2825))).toBe(false);
  });

  it('renders the leader for six STS3215s', () => {
    expect(resolveSo102IsLeader(bus(777))).toBe(true);
  });

  it('lets an explicit role override the bus', () => {
    expect(resolveSo102IsLeader(bus(2825), true)).toBe(true);
    expect(resolveSo102IsLeader(bus(777), false)).toBe(false);
  });
});
