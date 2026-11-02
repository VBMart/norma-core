import { classifySoArmBase } from '@/devices/so-arm-detection';
import { st3215Model } from '@/devices/st3215-model';
import {
  SO102_DEVICE_ID,
  SO102_MOTOR_COUNT,
  so102BasePos,
  so102BaseRpy,
  so102JointNames,
  so102UrdfPath,
} from './config';

export default st3215Model({
  id: SO102_DEVICE_ID,
  label: 'SO102',
  motorCount: SO102_MOTOR_COUNT,
  kinematics: {
    urdfPath: so102UrdfPath,
    basePos: so102BasePos,
    baseRpy: so102BaseRpy,
    jointNames: so102JointNames,
  },
  loadRenderer: () => import('./Renderer'),
  detectBus: (bus) => classifySoArmBase(bus) === 'so102',
});
