import type { RobotJointNames } from '@/st3215/robot-rendering/types';

export const SO102_DEVICE_ID = 'so102';
export const SO102_MOTOR_COUNT = 6;

// The SO-ARM 102 repository ships one URDF (follower geometry with the
// parallel gripper). The leader has no URDF, so both roles render this one,
// which matches how SO101 is shown today.
export const so102UrdfPath = 'devices/so102/so102_robot_follower.urdf';

// URDF is Z-up with base_link at the origin; the scene is Y-up.
export const so102BasePos: [number, number, number] = [0, 0, 0];
export const so102BaseRpy: [number, number, number] = [-Math.PI / 2, 0, 0];

// Motor 1..6 in bus order. Motor 6 drives the prismatic clamp1; clamp2
// mimics it in the URDF, so one joint name is enough.
export const so102JointNames: RobotJointNames = [
  'base_to_link1',
  'link1_to_link2',
  'link2_to_link3',
  'link3_to_link4',
  'link4_to_link5',
  'clamp1',
];
