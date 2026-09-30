import test from "node:test";
import assert from "node:assert/strict";
import { toCsv } from "./activity.js";

test("toCsv quotes fields and escapes embedded quotes", () => {
  const csv = toCsv([{ ts: 0, op: "verify", subject: 'a"b', outcome: "granted", score: 0.9, threshold: 0.4, detail: "match" }]);
  assert.match(csv.split("\n")[1], /"a""b"/);
});

test("toCsv neutralises formula-like subjects", () => {
  const csv = toCsv([{ ts: 0, op: "verify", subject: "=SUM(A1)", outcome: "denied" }]);
  assert.match(csv.split("\n")[1], /"'=SUM\(A1\)"/);
});
