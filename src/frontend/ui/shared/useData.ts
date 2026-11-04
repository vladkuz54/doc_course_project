"use client";

import { useCallback, useEffect, useState } from "react";

export function useData<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const reload = useCallback(
    () => load().then(setData, (e: Error) => setError(e.message)),
    [load],
  );

  useEffect(() => {
    reload();
  }, [reload]);

  const run = (action: () => Promise<unknown>, doneNotice = "") => {
    setError("");
    setNotice("");
    return action()
      .then(reload)
      .then(() => {
        setNotice(doneNotice);
        return true;
      })
      .catch((e: Error) => {
        setError(e.message);
        return false;
      });
  };

  return { data, error, notice, reload, run };
}
