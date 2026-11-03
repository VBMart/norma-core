import { classifySoArmBase } from '@/devices/so-arm-detection';
import { st3215Model } from '@/devices/st3215-model';
import {
  SO102_DEVICE_ID,
  SO102_MOTOR_COUNT,
  resolveSo102JointValue,
  resolveSo102UrdfPath,
  so102BasePos,
  so102BaseRpy,
  so102FollowerJointNames,
} from './config';

export default st3215Model({
  id: SO102_DEVICE_ID,
  label: 'SO102',
  motorCount: SO102_MOTOR_COUNT,
  // Joint-count lookups (NormVLA) have no role information; they get the
  // follower, whose gripper is what a policy acts on.
  kinematics: {
    urdfPath: resolveSo102UrdfPath(false),
    basePos: so102BasePos,
    baseRpy: so102BaseRpy,
    jointNames: so102FollowerJointNames,
    resolveJointValue: resolveSo102JointValue,
  },
  loadRenderer: () => import('./Renderer'),
  detectBus: (bus) => classifySoArmBase(bus) === 'so102',
});
