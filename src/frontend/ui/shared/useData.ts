"use client";

import { useCallback, useEffect, useState } from "react";

export function useData<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
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
  }, [reload]);

  const clearMessages = useCallback(() => {
    setError("");
    setNotice("");
  }, []);

  const run = (action: () => Promise<unknown>, doneNotice = "") => {
    clearMessages();
    setPending(true);
    return action()
      .then(reload)
      .then(() => {
        setNotice(doneNotice);
        return true;
      })
      .catch((e: Error) => {
        setError(e.message);
        return false;
      })
      .finally(() => setPending(false));
  };

  return { data, error, notice, pending, reload, run, clearMessages };
}
