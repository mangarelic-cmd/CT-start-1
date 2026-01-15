// File: src/fsutil.ts
// Purpose: Minimal FS helpers (Start-1). Robust on Windows + strict JSON.

import fs from "node:fs";
import path from "node:path";

export function ensureDir(p: string) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

export function readText(p: string): string {
  return fs.readFileSync(p, "utf8");
}

// UTF-8 sans BOM (robuste sur Windows)
export function writeText(p: string, t: string) {
  ensureDir(path.dirname(p));
  fs.writeFileSync(p, t, { encoding: "utf8" });
}

// JSON read avec fallback + erreur claire
export function readJson<T>(p: string, fallback: T): T {
  if (!fs.existsSync(p)) return fallback;
  const raw = fs.readFileSync(p, "utf8").trim();
  if (!raw) return fallback;

  try {
    return JSON.parse(raw) as T;
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(`Invalid JSON at ${p}: ${msg}`);
  }
}

export function writeJson(p: string, obj: unknown) {
  const txt = JSON.stringify(obj, null, 2) + "\n";
  writeText(p, txt);
}
