import { useEffect, useState } from 'react';
import Long from 'long';
import webSocketManager from '@/api/websocket';
import { normfs, startups } from '@/api/proto.js';

const STARTUPS_QUEUE = 'startups';
const MAX_STARTUPS = 1000;

export interface StartupMarker {
  frame: number;
  startupId: string;
  appStartId: string;
  version: string;
  gitHash: string;
}

let cachedMarkers: Promise<StartupMarker[]> | null = null;

function fetchStartupMarkers(): Promise<StartupMarker[]> {
  return new Promise((resolve, reject) => {
    const offset = new Uint8Array(Long.fromNumber(MAX_STARTUPS).toBytesLE());
    const stream = webSocketManager.normFs.read(
      STARTUPS_QUEUE,
      offset,
      normfs.OffsetType.OT_SHIFT_FROM_TAIL,
      MAX_STARTUPS,
    );

    const markers: StartupMarker[] = [];

    const onData = (event: Event) => {
      const readResponse = (event as CustomEvent).detail as normfs.IReadResponse;
      if (!readResponse.data) return;
      try {
        const data = readResponse.data instanceof Uint8Array
          ? readResponse.data
          : new Uint8Array(readResponse.data);
        const startup = startups.StationStartup.decode(data);
        if (!startup.inferenceQueuePtr || startup.inferenceQueuePtr.length === 0) return;
        const frame = Long.fromBytesLE(Array.from(startup.inferenceQueuePtr)).toNumber();
        const idBytes = readResponse.id?.raw;
        const startupId = idBytes
          ? Long.fromBytesLE(Array.from(idBytes as Uint8Array)).add(1).toString()
          : '';
        markers.push({
          frame,
          startupId,
          appStartId: startup.appStartId ? startup.appStartId.toString() : '',
          version: startup.version || '',
          gitHash: startup.gitHash || '',
        });
      } catch (err) {
        console.warn('[startupMarkers] failed to decode entry:', err);
      }
    };

    const onEnd = () => {
      cleanup();
      resolve(markers);
    };

    const onError = (event: Event) => {
      cleanup();
      reject((event as CustomEvent).detail);
    };

    const cleanup = () => {
      stream.removeEventListener('data', onData);
      stream.removeEventListener('end', onEnd);
      stream.removeEventListener('error', onError);
    };

    stream.addEventListener('data', onData);
    stream.addEventListener('end', onEnd);
    stream.addEventListener('error', onError);
  });
}

function loadStartupMarkers(): Promise<StartupMarker[]> {
  if (cachedMarkers === null) {
    cachedMarkers = fetchStartupMarkers().catch((err) => {
      cachedMarkers = null;
      throw err;
    });
  }
  return cachedMarkers;
}

export function useStartupMarkers(): StartupMarker[] {
  const [markers, setMarkers] = useState<StartupMarker[]>([]);

  useEffect(() => {
    let cancelled = false;

    const tryLoad = () => {
      if (cancelled) return;
      if (!webSocketManager.isConnected()) {
        window.setTimeout(tryLoad, 100);
        return;
      }
      loadStartupMarkers()
        .then((m) => {
          if (!cancelled) setMarkers(m);
        })
        .catch((err) => {
          console.error('Failed to load startup markers:', err);
        });
    };

    tryLoad();
    return () => {
      cancelled = true;
    };
  }, []);

  return markers;
}
