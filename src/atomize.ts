// File: src/atomize.ts
import { sha256, utcNow } from "./crypto.js";
import type { Claim } from "./types.js";

export function atomizeClaims(raw: string, uri: string, maxClaims: number): Claim[] {
  const lines = (raw || "")
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean);

  const k = Math.max(1, Math.floor(maxClaims || 1));
  const text = lines.slice(0, k).join("\n").trim();

  const id = sha256(`${uri}::::${text}`);

  return [
    {
      id,
      text,
      utc: utcNow()
    }
  ];
}
