import { useState, useEffect } from "react";
import { st3215 } from "@/api/proto";
import Long from "long";

// ---------------------------------------------------------------------------
// Configuration constants
// ---------------------------------------------------------------------------

const ERROR_PERSIST_NS = 5_000_000_000; // 5s - keep showing error after detection

// ---------------------------------------------------------------------------
// Type definitions
// ---------------------------------------------------------------------------

export interface ErrorPacketDump {
  motorId: number;
  errorKind: st3215.ST3215Error.ST3215ErrorKind;
  errorDescription: string;
  commandPacket: Uint8Array | null;
  responsePacket: Uint8Array | null;
  detectedAt: number; // timestamp when error was detected
}

export interface BusStatus {
  motorsCount: number; // Count of motors without errors
  errorDump: ErrorPacketDump | null; // Error packet info (persists for 5s)
}

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

function getMotorsCount(busState: st3215.InferenceState.IBusState | null): number {
  if (!busState?.motors) return 0;

  let count = 0;
  for (const motor of busState.motors) {
    if ((motor.error?.kind ?? 0) === 0) {
      count++;
    }
  }
  return count;
}

function extractErrorDump(busState: st3215.InferenceState.IBusState | null, currentStamp: number): ErrorPacketDump | null {
  if (!busState?.motors) return null;

  // Find first motor with error
  for (const motor of busState.motors) {
    const error = motor.error;
    const errorKind = error?.kind ?? 0;
    if (error && errorKind !== 0) {
      return {
        motorId: motor.id ?? 0,
        errorKind: errorKind,
        errorDescription: error.description ?? '',
        commandPacket: error.commandPacket ?? null,
        responsePacket: error.responsePacket ?? null,
        detectedAt: currentStamp,
      };
    }
  }

  return null;
}

function extractTimestamp(busState: st3215.InferenceState.IBusState | null): number {
  if (!busState?.monotonicStampNs) return 0;

  return Long.isLong(busState.monotonicStampNs)
    ? busState.monotonicStampNs.toNumber()
    : typeof busState.monotonicStampNs === 'number'
    ? busState.monotonicStampNs
    : 0;
}

// ---------------------------------------------------------------------------
// Bus Monitor Hook
// ---------------------------------------------------------------------------

export function useBusMonitor(busState: st3215.InferenceState.IBusState | null, ignoreErrors = false): BusStatus {
  const [status, setStatus] = useState<BusStatus>({
    motorsCount: 0,
    errorDump: null,
  });

  const [prevStamp, setPrevStamp] = useState<number>(0);
  const [persistedError, setPersistedError] = useState<ErrorPacketDump | null>(null);
  const [nextError, setNextError] = useState<ErrorPacketDump | null>(null); // Queue next error
  const [errorTimestamps, setErrorTimestamps] = useState<number[]>([]); // Track error timestamps

  useEffect(() => {
    const currentStamp = extractTimestamp(busState);

    if (currentStamp === 0) {
      setStatus({
        motorsCount: 0,
        errorDump: null,
      });
      return;
    }

    // Skip if timestamp hasn't advanced
    if (currentStamp <= prevStamp) {
      return;
    }

    setPrevStamp(currentStamp);

    const motorsCount = getMotorsCount(busState);

    // Check for new error (skip if ignoreErrors is true)
    const currentError = ignoreErrors ? null : extractErrorDump(busState, currentStamp);

    // Update error timestamps: add current timestamp if error detected, filter old ones
    const now = Date.now();
    const twoSecondsAgo = now - 2000;

    let recentErrorTimestamps = errorTimestamps.filter(ts => ts > twoSecondsAgo);

    if (currentError) {
      recentErrorTimestamps.push(now);
    }

    setErrorTimestamps(recentErrorTimestamps);

    // Only process error if we have 2+ errors in the last 2 seconds
    const shouldShowError = recentErrorTimestamps.length >= 2;
    const errorToProcess = shouldShowError ? currentError : null;

    let displayError: ErrorPacketDump | null = null;

    if (persistedError) {
      // We already have a persisted error - check if it's expired
      const timeSinceError = currentStamp - persistedError.detectedAt;
      if (timeSinceError < ERROR_PERSIST_NS) {
        // Still within 5s window - keep showing the original error
        displayError = persistedError;

        // If a new error comes in, queue it as next error
        if (errorToProcess && errorToProcess.detectedAt !== persistedError.detectedAt) {
          setNextError(errorToProcess);
        }
      } else {
        // Past 5s window - clear old error
        // Check if we have a queued error to show next
        if (nextError) {
          // Show the queued error with its original timestamp
          setPersistedError(nextError);
          setNextError(null);
          displayError = nextError;
        } else if (errorToProcess) {
          // No queued error, but new error detected
          setPersistedError(errorToProcess);
          displayError = errorToProcess;
        } else {
          // No errors at all
          setPersistedError(null);
          displayError = null;
        }
      }
    } else if (errorToProcess) {
      // No persisted error and new error detected (with 2+ in 2 seconds) - save it
      setPersistedError(errorToProcess);
      displayError = errorToProcess;
    }

    setStatus({
      motorsCount,
      errorDump: displayError,
    });
  }, [busState, prevStamp, persistedError, nextError, ignoreErrors, errorTimestamps]);

  return status;
}
