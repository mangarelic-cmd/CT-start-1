// File: src/cvm_bridge.ts
// Purpose: Execute embedded ct-cvm-mini without breaking dependencies.
// Notes:
// - Keeps the same exported function name/signature: runCvmMiniFromSiblingRepo(cslText, workDir, r_input?)
// - Keeps the same CVMOut type shape (adds no required fields).
// - Adds hardening: path checks, atomic temp filenames, strict JSON validation, safe phi-shape normalization.

import path from "node:path";
import fs from "node:fs";
import process from "node:process";
import { execFileSync } from "node:child_process";
import { readJson, writeJson, writeText, ensureDir } from "./fsutil.js";

export type CVMOut = {
  converged: boolean;
  iters: number;
  alignment_index: number;
  final: {
    phi: {
      PI: number;
      SQRT2: number;
      SQRT3: number;
      PHI: number;
      LN5: number;
    };
  };
  graph: unknown;
  trace: Array<{ iter: number; max_delta: number; energy: number }>;
};

function isFiniteNumber(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

function coerceMode(r_input?: number): string {
  if (!isFiniteNumber(r_input)) return "0.1";
  const s = r_input.toFixed(12).replace(/0+$/, "").replace(/\.$/, "");
  return s.length ? s : "0.1";
}

// Accepts 3 possible shapes for final.phi and normalizes to canonical:
// (A) {PI,SQRT2,SQRT3,PHI,LN5}
// (B) {pi,sqrt2,sqrt3,phi,ln5}
// (C) [PI,SQRT2,SQRT3,PHI,LN5]
function normalizePhi(phiRaw: unknown): { PI: number; SQRT2: number; SQRT3: number; PHI: number; LN5: number } {
  const keys = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"] as const;

  if (Array.isArray(phiRaw)) {
    if (phiRaw.length !== 5) {
      throw new Error(`Residual critical: final.phi array invalid (len=${phiRaw.length}).`);
    }
    const a = phiRaw as unknown[];
    const mapped: Record<(typeof keys)[number], unknown> = {
      PI: a[0],
      SQRT2: a[1],
      SQRT3: a[2],
      PHI: a[3],
      LN5: a[4],
    };
    for (const k of keys) {
      if (!isFiniteNumber(mapped[k])) {
        throw new Error(`Residual critical: final.phi[${k}] missing or invalid.`);
      }
    }
    return {
      PI: mapped.PI as number,
      SQRT2: mapped.SQRT2 as number,
      SQRT3: mapped.SQRT3 as number,
      PHI: mapped.PHI as number,
      LN5: mapped.LN5 as number,
    };
  }

  if (phiRaw && typeof phiRaw === "object") {
    const p = phiRaw as Record<string, unknown>;
    const get = (U: string, L: string) => (p[U] ?? p[L]);

    const mapped: Record<(typeof keys)[number], unknown> = {
      PI: get("PI", "pi"),
      SQRT2: get("SQRT2", "sqrt2"),
      SQRT3: get("SQRT3", "sqrt3"),
      PHI: get("PHI", "phi"),
      LN5: get("LN5", "ln5"),
    };

    for (const k of keys) {
      if (!isFiniteNumber(mapped[k])) {
        const present = Object.keys(p).slice(0, 60).join(",");
        throw new Error(`Residual critical: final.phi.${k} missing or invalid. Keys present: ${present}`);
      }
    }

    return {
      PI: mapped.PI as number,
      SQRT2: mapped.SQRT2 as number,
      SQRT3: mapped.SQRT3 as number,
      PHI: mapped.PHI as number,
      LN5: mapped.LN5 as number,
    };
  }

  throw new Error("Residual critical: final.phi invalid (not object or array).");
}

function extractPhiCandidate(out: unknown): unknown | undefined {
  if (!out || typeof out !== "object") return undefined;
  const o = out as Record<string, unknown>;
  const final = o["final"];
  if (final && typeof final === "object") {
    const f = final as Record<string, unknown>;
    if (f["phi"] !== undefined) return f["phi"];
    if (f["PHI"] !== undefined) return f["PHI"];
    if (f["Phi"] !== undefined) return f["Phi"];
  }
  if (o["phi"] !== undefined) return o["phi"];
  if (o["PHI"] !== undefined) return o["PHI"];
  return undefined;
}

function canonicalizeCvmOut(out: unknown): CVMOut {
  if (!out || typeof out !== "object") throw new Error("Residual critical: CVM output is not an object.");
  const o = out as Record<string, unknown>;
  const phiRaw = extractPhiCandidate(out);
  if (phiRaw === undefined) throw new Error("Residual critical: final.phi missing.");

  return {
    converged: o["converged"] as boolean,
    iters: o["iters"] as number,
    alignment_index: o["alignment_index"] as number,
    final: { phi: normalizePhi(phiRaw) },
    graph: o["graph"] ?? null,
    trace: (o["trace"] as CVMOut["trace"]) ?? [],
  };
}

function assertCvmOut(out: unknown): asserts out is CVMOut {
  if (!out || typeof out !== "object") throw new Error("Residual critical: CVM output is not an object.");

  const o = out as Record<string, unknown>;

  if (!isFiniteNumber(o["alignment_index"])) throw new Error("Residual critical: alignment_index missing or invalid.");
  if (typeof o["converged"] !== "boolean") throw new Error("Residual critical: converged missing or invalid.");
  if (!Number.isInteger(o["iters"]) || (o["iters"] as number) < 0) throw new Error("Residual critical: iters missing or invalid.");

  const final = o["final"];
  if (!final || typeof final !== "object") throw new Error("Residual critical: final missing.");

  const finalObj = final as Record<string, unknown>;
  const phiRaw = finalObj["phi"];
  if (phiRaw === undefined) throw new Error("Residual critical: final.phi missing.");

  // Normalize and re-inject canonical phi so downstream code always sees uppercase object.
  const phiNorm = normalizePhi(phiRaw);
  finalObj["phi"] = phiNorm;

  if (!Array.isArray(o["trace"])) throw new Error("Residual critical: trace missing or invalid.");
}

function safeUnlink(p: string) {
  try {
    if (fs.existsSync(p)) fs.unlinkSync(p);
  } catch {
    // ignore
  }
}

function resolveStart1Root(workDir: string): string {
  const candidate = path.resolve(workDir);
  const cliPath = path.join(candidate, "ct-cvm-mini", "dist", "cli.js");
  if (fs.existsSync(cliPath)) return candidate;

  const cwd = process.cwd();
  const cliFromCwd = path.join(cwd, "ct-cvm-mini", "dist", "cli.js");
  if (fs.existsSync(cliFromCwd)) return cwd;

  throw new Error("ct-cvm-mini introuvable au chemin canonique.");
}

export function runCvmMiniFromSiblingRepo(cslText: string, workDir: string, r_input?: number): CVMOut {
  const start1Root = resolveStart1Root(workDir);
  const cvmCli = path.join(start1Root, "ct-cvm-mini", "dist", "cli.js");

  const tmpDir = path.resolve(start1Root, "data", "out", "logs");
  ensureDir(tmpDir);

  const stamp = `${Date.now()}_${process.pid}_${Math.random().toString(16).slice(2)}`;
  const inCsl = path.join(tmpDir, `tmp_input_${stamp}.csl`);
  const outJson = path.join(tmpDir, `tmp_cvm_out_${stamp}.json`);
  const stableIn = path.join(tmpDir, "tmp_cvm_in.csl");
  const stableOut = path.join(tmpDir, "tmp_cvm_out.json");

  writeText(inCsl, cslText);
  writeText(stableIn, cslText);

  try {
    execFileSync("node", [cvmCli, "run", inCsl, outJson], { stdio: "inherit" });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    safeUnlink(inCsl);
    safeUnlink(outJson);
    throw new Error(`CVM execution failed: ${msg}`);
  }

  const out = readJson<CVMOut>(outJson, (null as unknown) as CVMOut);
  let canon: CVMOut;
  try {
    canon = canonicalizeCvmOut(out);
    assertCvmOut(canon);
  } catch (e: unknown) {
    const rawPath = path.join(tmpDir, "cvm_out.raw.json");
    writeJson(rawPath, out as Record<string, unknown>);
    throw e;
  }
  writeJson(stableOut, canon);

  safeUnlink(inCsl);
  safeUnlink(outJson);

  void r_input;
  void coerceMode;

  return canon;
}
