import { classifySoArmBase } from '@/devices/so-arm-detection';
import { st3215Model } from '@/devices/st3215-model';
import {
  SO101_DEVICE_ID,
  SO101_MOTOR_COUNT,
  resolveSo101UrdfPath,
  so101BasePos,
  so101BaseRpy,
  so101JointNames,
} from './config';

export default st3215Model({
  id: SO101_DEVICE_ID,
  label: 'SO101',
  motorCount: SO101_MOTOR_COUNT,
  // SO101 and SO102 leaders are both six STS3215s; SO101 stays the default
  // until the user picks a model for the bus.
  defaultForMotorCount: true,
  kinematics: {
    urdfPath: resolveSo101UrdfPath(false),
    basePos: so101BasePos,
    baseRpy: so101BaseRpy,
    jointNames: so101JointNames,
  },
  loadRenderer: () => import('./Renderer'),
  detectBus: (bus) => classifySoArmBase(bus) === 'so101',
});
