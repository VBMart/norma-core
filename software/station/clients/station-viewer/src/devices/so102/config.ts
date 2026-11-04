import type { st3215 } from '@/api/proto.js';
import { isSo102FollowerBus } from '@/devices/so-arm-detection';
import type {
  JointValueContext,
  MotorMaterialContext,
  RobotJointNames,
} from '@/st3215/robot-rendering/types';

export const SO102_DEVICE_ID = 'so102';
export const SO102_MOTOR_COUNT = 6;

// Both URDFs are built from the SO-ARM 102 repository: the follower is the
// upstream URDF, the leader swaps link 5 for the wrist-roll part, handle and
// trigger taken from the leader assembly.
export function resolveSo102UrdfPath(isLeader: boolean): string {
  return isLeader
    ? 'devices/so102/so102_robot_leader.urdf'
    : 'devices/so102/so102_robot_follower.urdf';
}

// URDF is Z-up with base_link at the origin; the scene is Y-up.
export const so102BasePos: [number, number, number] = [0, 0, 0];
export const so102BaseRpy: [number, number, number] = [-Math.PI / 2, 0, 0];

const SO102_ARM_JOINT_NAMES = [
  'base_to_link1',
  'link1_to_link2',
  'link2_to_link3',
  'link3_to_link4',
  'link4_to_link5',
];

// Motor 6 is listed as a one-element group so the renderer routes it through
// resolveSo102JointValue (plain joint names bypass the resolver).
export const so102FollowerJointNames: RobotJointNames = [...SO102_ARM_JOINT_NAMES, ['clamp1']];
export const so102LeaderJointNames: RobotJointNames = [...SO102_ARM_JOINT_NAMES, ['trigger']];

/**
 * Leader unless the caller says otherwise or the bus carries follower servos
 * (STS3235/STS3250); a six-STS3215 bus recognised as SO102 is a leader.
 */
export function resolveSo102IsLeader(
  bus: st3215.InferenceState.IBusState,
  isLeader?: boolean,
): boolean {
  return isLeader ?? !isSo102FollowerBus(bus);
}

export function resolveSo102JointNames(isLeader: boolean): RobotJointNames {
  return isLeader ? so102LeaderJointNames : so102FollowerJointNames;
}

/**
 * Motor 6 runs opposite to the URDF joints: its calibrated minimum is the
 * open gripper / released trigger, which both URDFs put at the upper limit
 * (clamp1 fully apart, trigger at 0).
 */
export function resolveSo102JointValue({
  position,
  lowerLimit,
  upperLimit,
}: JointValueContext): number {
  return upperLimit - position * (upperLimit - lowerLimit);
}

const MOTOR_MATERIAL_PATTERN = /^so102_motor_(\d+)_material$/;

export function resolveSo102MotorMaterialIndex({
  materialName,
  motorCount,
}: MotorMaterialContext): number | null {
  const match = MOTOR_MATERIAL_PATTERN.exec(materialName);
  if (!match) {
    return null;
  }
  const motorIndex = Number.parseInt(match[1], 10) - 1;
  return motorIndex >= 0 && motorIndex < motorCount ? motorIndex : null;
}
