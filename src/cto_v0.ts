// File: src/cto_v0.ts
// Purpose: CTO-UCT proxy — structural 5D address vector (NOT semantics).

import zlib from "node:zlib";
import type { Mode5, Vector5 } from "./types.js";

const MODES: Mode5[] = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"];

export type CTOResult = {
  vector: Vector5;
  dominance: Mode5;
  diagnostics: {
    bytes: number;
    gzip_ratio: number;   // compressed / raw
    pi_stability: number; // [0..1]
    ln5_noise: number;    // [0..1]
    token_count: number;
    unique_ratio: number; // unique_tokens / tokens
  };
};

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

function safeDiv(a: number, b: number): number {
  return b === 0 ? 0 : a / b;
}

function normalizeTextForStructure(s: string): string {
  return s.replace(/\r\n/g, "\n").replace(/[ \t]+/g, " ").trim();
}

function gzipRatioUtf8(s: string): number {
  const buf = Buffer.from(s, "utf8");
  if (buf.length === 0) return 1.0;
  const gz = zlib.gzipSync(buf, { level: 9 });
  return gz.length / buf.length;
}

function tokenizeUnicode(s: string): string[] {
  const re = /(\p{L}+|\p{N}+|[^\p{L}\p{N}\s])/gu;
  const out: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(s)) !== null) out.push(m[0]);
  return out;
}

function countRegex(s: string, re: RegExp): number {
  const m = s.match(re);
  return m ? m.length : 0;
}

function shannonEntropyBytesUtf8(s: string): number {
  const buf = Buffer.from(s, "utf8");
  if (buf.length === 0) return 0;
  const freq = new Array<number>(256).fill(0);
  for (const b of buf) freq[b]++;
  const n = buf.length;
  let H = 0;
  for (let i = 0; i < 256; i++) {
    if (freq[i] === 0) continue;
    const p = freq[i] / n;
    H -= p * Math.log2(p);
  }
  return H / 8;
}

function argmaxVector(v: Vector5): Mode5 {
  let best: Mode5 = "PI";
  let bestVal = -Infinity;
  for (const m of MODES) {
    if (v[m] > bestVal) { bestVal = v[m]; best = m; }
  }
  return best;
}

export function transposeToVector(text: string): CTOResult {
  const s0 = normalizeTextForStructure(text);
  const bytes = Buffer.byteLength(s0, "utf8");

  const gr = gzipRatioUtf8(s0);
  const H = shannonEntropyBytesUtf8(s0);
  const tokens = tokenizeUnicode(s0);
  const token_count = tokens.length;

  const uniq = new Set(tokens);
  const unique_ratio = token_count > 0 ? uniq.size / token_count : 1;

  const punct = countRegex(s0, /[.,;:!?]/g);
  const brackets = countRegex(s0, /[\(\)\[\]\{\}<>]/g);
  const quotes = countRegex(s0, /["'«»“”‘’]/g);

  const connectors = countRegex(s0, /(::|->|=>|==|!=|<=|>=|=|:|\/|\\|\||&|@|#)/g);
  const flowOps = countRegex(s0, /(->|=>|~>|<-|\+\+|--|\+|-|\*|\/|%|\^)/g);
  const newlines = countRegex(s0, /\n/g);

  const compressibility = clamp01(1.0 - clamp01(gr));
  const repetition = clamp01(1.0 - clamp01(unique_ratio));
  const stability = clamp01(0.60 * compressibility + 0.40 * repetition);

  const noise = clamp01(0.55 * clamp01(gr) + 0.45 * clamp01(H));

  const denom = Math.max(1, bytes);

  const sqrt2_raw =
    safeDiv(connectors, denom) * 6000 +
    safeDiv(countRegex(s0, /[,]/g), denom) * 4000;

  const sqrt3_raw =
    safeDiv(punct + brackets + quotes, denom) * 7000 +
    safeDiv(newlines, denom) * 3000;

  const phi_raw =
    safeDiv(flowOps, denom) * 8000 +
    safeDiv(countRegex(s0, /\d{1,4}[-/:]\d{1,2}[-/:]\d{1,4}/g), denom) * 4000;

  const raw: Vector5 = {
    PI: stability,
    SQRT2: clamp01(sqrt2_raw),
    SQRT3: clamp01(sqrt3_raw),
    PHI: clamp01(phi_raw),
    LN5: noise
  };

  const sum = MODES.reduce((a, m) => a + raw[m], 0);
  const denom2 = sum > 0 ? sum : 1;

  const vector: Vector5 = {
    PI: raw.PI / denom2,
    SQRT2: raw.SQRT2 / denom2,
    SQRT3: raw.SQRT3 / denom2,
    PHI: raw.PHI / denom2,
    LN5: raw.LN5 / denom2
  };

  return {
    vector,
    dominance: argmaxVector(vector),
    diagnostics: {
      bytes,
      gzip_ratio: gr,
      pi_stability: stability,
      ln5_noise: noise,
      token_count,
      unique_ratio
    }
  };
}
