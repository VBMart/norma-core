import { useCallback, useSyncExternalStore } from 'react';

/**
 * Which registered ST3215 model the user picked for a bus, keyed by bus
 * serial number. Needed where motor count alone is ambiguous (SO101 and
 * SO102 leaders are both six STS3215s). Persisted in localStorage so the
 * choice survives reloads; falls back to memory when storage is blocked.
 */

const STORAGE_PREFIX = 'st3215-model:';

const memory = new Map<string, string>();
const listeners = new Set<() => void>();

function storage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage;
  } catch {
    return null;
  }
}

function storageKey(busSerial: string): string {
  return `${STORAGE_PREFIX}${busSerial}`;
}

export function getSt3215ModelSelection(busSerial: string | null | undefined): string | null {
  if (!busSerial) {
    return null;
  }
  try {
    const stored = storage()?.getItem(storageKey(busSerial));
    if (stored) {
      return stored;
    }
  } catch {
    // Fall through to the in-memory copy.
  }
  return memory.get(busSerial) ?? null;
}

export function setSt3215ModelSelection(busSerial: string, modelId: string | null): void {
  if (modelId) {
    memory.set(busSerial, modelId);
  } else {
    memory.delete(busSerial);
  }
  try {
    const store = storage();
    if (modelId) {
      store?.setItem(storageKey(busSerial), modelId);
    } else {
      store?.removeItem(storageKey(busSerial));
    }
  } catch {
    // Memory copy already updated.
  }
  listeners.forEach((listener) => listener());
}

export function subscribeSt3215ModelSelection(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useSt3215ModelSelection(
  busSerial: string | null | undefined,
): [string | null, (modelId: string | null) => void] {
  const selection = useSyncExternalStore(
    subscribeSt3215ModelSelection,
    () => getSt3215ModelSelection(busSerial),
    () => getSt3215ModelSelection(busSerial),
  );
  const setSelection = useCallback(
    (modelId: string | null) => {
      if (busSerial) {
        setSt3215ModelSelection(busSerial, modelId);
      }
    },
    [busSerial],
  );
  return [selection, setSelection];
}
