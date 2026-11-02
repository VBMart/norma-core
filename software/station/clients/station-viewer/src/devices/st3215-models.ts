import type { st3215 } from '@/api/proto.js';
import type { St3215Kinematics, St3215Model } from './st3215-model';

function createSt3215ModelCatalog(models: readonly St3215Model[]) {
  const modelsByMotorCount = new Map<number, St3215Model[]>();
  const modelIds = new Set<string>();

  for (const model of models) {
    if (!model.id) {
      throw new Error('ST3215 model id must not be empty.');
    }
    if (modelIds.has(model.id)) {
      throw new Error(`Duplicate ST3215 model id: ${model.id}`);
    }
    if (!Number.isInteger(model.motorCount) || model.motorCount <= 0) {
      throw new Error(`ST3215 model ${model.id} has an invalid motor count.`);
    }

    modelIds.add(model.id);
    const group = modelsByMotorCount.get(model.motorCount) ?? [];
    group.push(model);
    modelsByMotorCount.set(model.motorCount, group);
  }

  for (const [motorCount, group] of modelsByMotorCount) {
    const defaults = group.filter((model) => model.defaultForMotorCount);
    if (group.length > 1 && defaults.length !== 1) {
      throw new Error(
        `ST3215 motor count ${motorCount} is shared by ${group.map((model) => model.id).join(', ')}; exactly one of them must set defaultForMotorCount.`,
      );
    }
    // Default first, then registration order, so option lists are stable.
    group.sort((a, b) => Number(b.defaultForMotorCount) - Number(a.defaultForMotorCount));
  }

  function pick<T>(candidates: readonly T[], preferredModelId: string | null | undefined, idOf: (candidate: T) => string): T | null {
    if (candidates.length === 0) {
      return null;
    }
    if (preferredModelId) {
      const preferred = candidates.find((candidate) => idOf(candidate) === preferredModelId);
      if (preferred) {
        return preferred;
      }
    }
    return candidates[0];
  }

  return {
    listModels(bus: st3215.InferenceState.IBusState): St3215Model[] {
      const group = modelsByMotorCount.get(bus.motors?.length ?? 0) ?? [];
      return group.filter((model) => model.supportsBus(bus));
    },
    detectBus(bus: st3215.InferenceState.IBusState): St3215Model | null {
      const detected = this.listModels(bus).filter((model) => model.detectsBus(bus));
      return detected.length === 1 ? detected[0] : null;
    },
    resolveBus(
      bus: st3215.InferenceState.IBusState,
      preferredModelId?: string | null,
    ): St3215Model | null {
      return this.detectBus(bus)
        ?? pick(this.listModels(bus), preferredModelId, (model) => model.id);
    },
    resolveJointCount(
      jointCount: number,
      preferredModelId?: string | null,
    ): St3215Kinematics | null {
      const group = modelsByMotorCount.get(jointCount) ?? [];
      const candidates = group.filter((model) => model.supportsJointCount(jointCount));
      return pick(candidates, preferredModelId, (model) => model.id)?.kinematics ?? null;
    },
  };
}

const st3215ModelEntries = import.meta.glob<{ default: St3215Model }>(
  './*/st3215-model.ts',
  { eager: true },
);

const st3215ModelCatalog = createSt3215ModelCatalog(
  Object.values(st3215ModelEntries).map((entry) => entry.default),
);

/**
 * Every registered model that can render this bus. More than one entry means
 * the bus is ambiguous (same motor count) and the user has to choose.
 */
export function listSt3215Models(
  bus: st3215.InferenceState.IBusState,
): St3215Model[] {
  return st3215ModelCatalog.listModels(bus);
}

/**
 * The model the bus data identifies on its own (for SO-ARMs, from the base
 * motor's frozen calibration range), or null while it is undecided.
 */
export function detectSt3215Model(
  bus: st3215.InferenceState.IBusState,
): St3215Model | null {
  return st3215ModelCatalog.detectBus(bus);
}

/**
 * The model to render for this bus: the detected one when the bus data is
 * conclusive, else the preferred one when it fits, else the default for its
 * motor count.
 */
export function resolveSt3215Model(
  bus: st3215.InferenceState.IBusState,
  preferredModelId?: string | null,
): St3215Model | null {
  return st3215ModelCatalog.resolveBus(bus, preferredModelId);
}

export function supportsSt3215Bus(bus: st3215.InferenceState.IBusState): boolean {
  return resolveSt3215Model(bus) !== null;
}

export function resolveSt3215Kinematics(
  jointCount: number,
  preferredModelId?: string | null,
): St3215Kinematics | null {
  return st3215ModelCatalog.resolveJointCount(jointCount, preferredModelId);
}
