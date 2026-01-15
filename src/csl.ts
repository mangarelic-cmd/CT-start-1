// File: src/csl.ts
// Purpose: Convert Vector5 to CSL text for ct-cvm-mini.
// Rule: strict, deterministic formatting (UTF-8 without BOM when written by fsutil).

import type { Vector5 } from "./types.js";

function finite01(x: unknown): number {
  const n = typeof x === "number" ? x : Number(x);
  if (!Number.isFinite(n)) return 0;
  if (n < 0) return 0;
  if (n > 1) return 1;
  return n;
}

/**
 * CSL format expected by ct-cvm-mini parser:
 * node <ID>
 * edge <A> <B> w=<float>
 * flow <A> -> <B> k=<float>
 * pin <ID> <float> (used only for dominant injection)
 */
export function vectorToCSLText(v: Vector5): string {
  const keys: (keyof Vector5)[] = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"];
  const vals: Record<keyof Vector5, number> = {
    PI: finite01(v.PI),
    SQRT2: finite01(v.SQRT2),
    SQRT3: finite01(v.SQRT3),
    PHI: finite01(v.PHI),
    LN5: finite01(v.LN5),
  };

  let dominant: keyof Vector5 = "PI";
  let maxV = -1;
  for (const k of keys) {
    const val = vals[k];
    if (val > maxV) {
      maxV = val;
      dominant = k;
    }
  }

  // Fixed decimal width => stable diffs + stable downstream parsing.
  const f = (x: number) => x.toFixed(6);
  const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
  const wFor = (a: number, b: number) => clamp01(0.02 + 0.18 * ((a + b) / 2));
  const kFor = (a: number, b: number) => clamp01(0.01 + 0.09 * Math.abs(a - b));
  const dFor = (x: number) => clamp01(0.01 + 0.08 * (1 - x));

  const lines: string[] = [];
  for (const k of keys) lines.push(`node ${k}`);
  for (const k of keys) lines.push(`decay ${k} ${f(dFor(vals[k]))}`);

  // Inject only the dominant component to avoid trivial all-pins.
  if (maxV > 0) {
    lines.push(`pin ${dominant} ${f(maxV)}`);
  }

  for (const k of keys) {
    if (k === dominant) continue;
    const w = wFor(vals[dominant], vals[k]);
    lines.push(`edge ${dominant} ${k} w=${f(w)}`);

    const kVal = kFor(vals[dominant], vals[k]);
    if (vals[dominant] >= vals[k]) {
      lines.push(`flow ${dominant} -> ${k} k=${f(kVal)}`);
    } else {
      lines.push(`flow ${k} -> ${dominant} k=${f(kVal)}`);
    }
  }

  return lines.join("\n") + "\n";
}

export function parseCSLText(txt: string): Vector5 {
  const out: Vector5 = { PI: 0, SQRT2: 0, SQRT3: 0, PHI: 0, LN5: 0 };
  const lines = (txt || "").split(/\r?\n/);
  for (const line of lines) {
    const m = line.match(/^\s*pin\s+(PI|SQRT2|SQRT3|PHI|LN5)\s+([+-]?\d+(\.\d+)?)\s*$/);
    if (!m) continue;
    const k = m[1] as keyof Vector5;
    const v = Number(m[2]);
    out[k] = Number.isFinite(v) ? v : 0;
  }
  return out;
}
