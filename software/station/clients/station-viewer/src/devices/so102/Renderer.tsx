import { forwardRef } from 'react';
import BaseRobotRenderer from '@/st3215/robot-rendering/BaseRobotRenderer';
import type {
  BaseRobotRendererRef,
  St3215RobotRendererProps,
} from '@/st3215/robot-rendering/types';
import {
  so102BasePos,
  so102BaseRpy,
  so102JointNames,
  so102UrdfPath,
} from './config';

// The SO102 URDF uses one shared material, so motors cannot be coloured by
// status the way SO101/ElRobot are; no material resolver is passed.
const SO102DeviceRenderer = forwardRef<BaseRobotRendererRef, St3215RobotRendererProps>(
  function SO102DeviceRenderer({ busSerialNumber, bus, isLeader }, ref) {
    return (
      <BaseRobotRenderer
        ref={ref}
        busSerialNumber={busSerialNumber}
        bus={bus}
        isLeader={isLeader}
        urdfPath={so102UrdfPath}
        jointNames={so102JointNames}
        basePos={so102BasePos}
        baseRpy={so102BaseRpy}
      />
    );
  },
);

export default SO102DeviceRenderer;
