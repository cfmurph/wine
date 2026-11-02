"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface FetchState<T> {
  data: T | null;
  failed: boolean;
  settledKey: string | null;
}

/**
 * Load data when `key` changes, ignoring responses that arrive after a newer request started.
 * A null key means "don't load yet". Earlier data stays available while newer data loads.
 */
export function useFetch<T>(key: string | null, fetcher: () => Promise<T>, delayMs = 0) {
  const [state, setState] = useState<FetchState<T>>({ data: null, failed: false, settledKey: null });
  const latestFetcher = useRef(fetcher);

  useEffect(() => {
    latestFetcher.current = fetcher;
  });

  useEffect(() => {
    if (key === null) return;
    let current = true;
    const timer = setTimeout(() => {
      latestFetcher
        .current()
        .then((data) => {
          if (current) setState({ data, failed: false, settledKey: key });
        })
        .catch(() => {
          if (current) setState((previous) => ({ ...previous, failed: true, settledKey: key }));
        });
    }, delayMs);
    return () => {
      current = false;
      clearTimeout(timer);
    };
  }, [key, delayMs]);

  const setData = useCallback((update: (data: T | null) => T | null) => {
    setState((previous) => ({ ...previous, data: update(previous.data) }));
  }, []);

  return {
    data: state.data,
    failed: state.failed && state.settledKey === key,
    loading: key !== null && state.settledKey !== key,
    setData,
  };
}
