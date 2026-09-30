"use client";

import { useState } from "react";
import { addActivity } from "./activity";
import { describeDecision } from "@/components/Decision";

/** Runs a verify/identify call, tracks its lifecycle and records the outcome in the activity log. */
export default function useDecisionRunner(mode) {
  const [busy, setBusy] = useState(false);
  const [body, setBody] = useState(null);
  const [error, setError] = useState(null);

  async function run(subject, call) {
    setBusy(true);
    setError(null);
    try {
      const result = await call();
      setBody(result);
      addActivity({
        op: mode, subject: subject || result.person_id || "(unknown)", outcome: describeDecision(mode, result).outcome,
        score: result.score, threshold: result.threshold, detail: result.status,
      });
    } catch (e) {
      setBody(null);
      setError(e.message);
      addActivity({ op: mode, subject: subject || "(unknown)", outcome: "error", detail: e.message });
    } finally {
      setBusy(false);
    }
  }
  return { busy, body, error, run };
}
