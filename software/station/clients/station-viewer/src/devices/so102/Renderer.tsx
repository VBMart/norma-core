import { forwardRef } from 'react';
import BaseRobotRenderer from '@/st3215/robot-rendering/BaseRobotRenderer';
import type {
  BaseRobotRendererRef,
  St3215RobotRendererProps,
} from '@/st3215/robot-rendering/types';
import {
  resolveSo102IsLeader,
  resolveSo102JointNames,
  resolveSo102JointValue,
  resolveSo102MotorMaterialIndex,
  resolveSo102UrdfPath,
  so102BasePos,
  so102BaseRpy,
} from './config';

const SO102DeviceRenderer = forwardRef<BaseRobotRendererRef, St3215RobotRendererProps>(
  function SO102DeviceRenderer({ busSerialNumber, bus, isLeader }, ref) {
    const leader = resolveSo102IsLeader(bus, isLeader);
    return (
      <BaseRobotRenderer
        ref={ref}
        busSerialNumber={busSerialNumber}
        bus={bus}
        isLeader={leader}
        urdfPath={resolveSo102UrdfPath(leader)}
        jointNames={resolveSo102JointNames(leader)}
        basePos={so102BasePos}
        baseRpy={so102BaseRpy}
        resolveMotorMaterialIndex={resolveSo102MotorMaterialIndex}
        resolveJointValue={resolveSo102JointValue}
      />
    );
  },
);

export default SO102DeviceRenderer;
