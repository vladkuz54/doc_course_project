"use client";

import { useCallback, useEffect, useState } from "react";

export const REFRESH_EVENT = "fleet:refresh";

export function useData<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [warning, setWarning] = useState("");
  const [pending, setPending] = useState(false);

  const reload = useCallback(
    () =>
      load().then(
        (loaded) => {
          setData(loaded);
          setError("");
        },
        (e: Error) => setError(e.message),
      ),
    [load],
  );

  useEffect(() => {
    reload();
    window.addEventListener(REFRESH_EVENT, reload);
    return () => window.removeEventListener(REFRESH_EVENT, reload);
  }, [reload]);

  const clearMessages = useCallback(() => {
    setError("");
    setNotice("");
    setWarning("");
  }, []);

  const run = useCallback(
    (action: () => Promise<unknown>, doneNotice = "") => {
      clearMessages();
      setPending(true);
      return action()
        .then(load)
        .then((loaded) => {
          setData(loaded);
          setNotice(doneNotice);
          return true;
        })
        .catch((e: Error) => {
          setError(e.message);
          return false;
        })
        .finally(() => setPending(false));
    },
    [load, clearMessages],
  );

  return {
    data,
    error,
    notice,
    warning,
    pending,
    reload,
    run,
    setWarning,
    clearMessages,
  };
}
