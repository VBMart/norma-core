import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

function createFakeStorage(): Storage {
  const store = new Map<string, string>();
  return {
    get length() {
      return store.size;
    },
    clear: () => store.clear(),
    getItem: (key: string) => store.get(key) ?? null,
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    removeItem: (key: string) => {
      store.delete(key);
    },
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
  };
}

describe('ST3215 model selection store', () => {
  let storage: Storage;

  beforeEach(() => {
    storage = createFakeStorage();
    vi.stubGlobal('window', { localStorage: storage });
    vi.resetModules();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  async function loadStore() {
    return import('./st3215-model-selection');
  }

  it('returns null for a bus with no stored selection', async () => {
    const store = await loadStore();
    expect(store.getSt3215ModelSelection('ABC')).toBeNull();
    expect(store.getSt3215ModelSelection(null)).toBeNull();
    expect(store.getSt3215ModelSelection(undefined)).toBeNull();
  });

  it('persists a selection per bus serial and notifies subscribers', async () => {
    const store = await loadStore();
    const listener = vi.fn();
    const unsubscribe = store.subscribeSt3215ModelSelection(listener);

    store.setSt3215ModelSelection('ABC', 'so102');

    expect(store.getSt3215ModelSelection('ABC')).toBe('so102');
    expect(store.getSt3215ModelSelection('XYZ')).toBeNull();
    expect(listener).toHaveBeenCalledTimes(1);
    expect(storage.getItem('st3215-model:ABC')).toBe('so102');

    unsubscribe();
    store.setSt3215ModelSelection('ABC', 'so101');
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('reads a selection stored by an earlier page load', async () => {
    storage.setItem('st3215-model:ABC', 'so102');
    const store = await loadStore();
    expect(store.getSt3215ModelSelection('ABC')).toBe('so102');
  });

  it('clears a selection when set to null', async () => {
    const store = await loadStore();
    store.setSt3215ModelSelection('ABC', 'so102');
    store.setSt3215ModelSelection('ABC', null);
    expect(store.getSt3215ModelSelection('ABC')).toBeNull();
    expect(storage.getItem('st3215-model:ABC')).toBeNull();
  });

  it('keeps working in memory when localStorage is unavailable', async () => {
    vi.stubGlobal('window', {
      get localStorage(): Storage {
        throw new Error('blocked');
      },
    });
    const store = await loadStore();
    store.setSt3215ModelSelection('ABC', 'so102');
    expect(store.getSt3215ModelSelection('ABC')).toBe('so102');
  });
});
