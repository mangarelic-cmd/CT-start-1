// File: src/crypto.ts
// Purpose: Canonicalization + hashing utilities (Start-1). Deterministic across runs.

import * as crypto from "node:crypto";

type JsonValue = null | boolean | number | string | JsonValue[] | { [k: string]: JsonValue };

function isPlainObject(x: unknown): x is Record<string, unknown> {
  return !!x && typeof x === "object" && !Array.isArray(x);
}

function sortJson(value: unknown): JsonValue {
  if (value === null) return null;

  if (typeof value === "boolean") return value;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string") return value;

  if (Array.isArray(value)) return value.map(sortJson);

  if (isPlainObject(value)) {
    const out: { [k: string]: JsonValue } = {};
    for (const k of Object.keys(value).sort()) {
      out[k] = sortJson(value[k]);
    }
    return out;
  }

  // functions, symbols, undefined, bigint, etc => stringify as string tag
  return String(value) as unknown as JsonValue;
}

export function canonicalize(value: unknown): string {
  return JSON.stringify(sortJson(value), null, 2) + "\n";
}

export function sha256(text: string): string {
  return crypto.createHash("sha256").update(text).digest("hex");
}

export function utcNow(): string {
  return new Date().toISOString();
}

export function normText(s: string): string {
  return s.replace(/\s+/g, " ").trim().toLowerCase();
}
