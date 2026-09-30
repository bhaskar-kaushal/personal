"use client";

import { useEffect, useState } from "react";
import { loadActivity } from "./activity";

/** Activity rows from localStorage, kept in sync across components and tabs. */
export default function useActivity() {
  const [rows, setRows] = useState(null);
  useEffect(() => {
    const sync = () => setRows(loadActivity());
    sync();
    window.addEventListener("facegate:activity", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("facegate:activity", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);
  return rows;
}
