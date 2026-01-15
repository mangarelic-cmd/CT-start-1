// File: src/pipeline.ts
// Purpose: Start-1 ingestion pipeline (CT) ? threshold-gated calibration (0.66/0.787/0.87/0.946/0.995204) without breaking dependencies.

import path from "node:path";
import fs from "node:fs";
import { canonicalize, utcNow } from "./crypto.js";
import { atomizeClaims } from "./atomize.js";
import { transposeToVector } from "./cto_v0.js";
import { vectorToCSLText } from "./csl.js";
import { packetId, skinId, residueId } from "./dedup.js";
import { runCvmMiniFromSiblingRepo, type CVMOut } from "./cvm_bridge.js";
import { readJson, writeJson, ensureDir, writeText } from "./fsutil.js";
import type {
  CausalPacket,
  Skin,
  Residue,
  DedupDecision,
  ResiduePool,
  Vector5,
  Mode5,
  ResidueAgeBand
} from "./types.js";
import { newPool, depositResidue } from "./residue_pool.js";

// --------------------
// CT Threshold Gates (Start-1 locked)
// --------------------
const I_ENTRY = 0.66;        // minimal chemical form (entry into consideration)
const I_STABLE = 0.787;      // stable projection (merge-eligible, but not "physical")
const I_ANCHOR = 0.87;       // physical anchor / energy barrier (core-merge allowed later)
const I_CRITICAL = 0.946;    // SUTURE / SKIN admission
const I_HORIZON = 0.995204;  // CT near-identity horizon (replace old 0.99975)

// CT constants (fixed)
const PI = Math.PI;
const PHI = (1 + Math.sqrt(5)) / 2;

function safeNum(x: unknown, fallback = 0): number {
  return typeof x === "number" && Number.isFinite(x) ? x : fallback;
}

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

function clampHorizon(x: number): number {
  if (!Number.isFinite(x)) return 0;
  const y = Math.max(0, x);
  return Math.min(I_HORIZON, y);
}

function isFiniteNumber(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

function assertInvariants(input: {
  cvm: CVMOut;
  tmpCvmOutPath: string;
  packet: CausalPacket;
  skin: Skin;
  residue: Residue;
  absorption: Vector5;
  packetPath: string;
  skinPath: string;
  residuePath: string;
}) {
  const fail = (field: string, filePath: string, details?: string) => {
    const extra = details ? ` (${details})` : "";
    throw new Error(`Invariant failed: ${field} @ ${filePath}${extra}`);
  };

  const { cvm, tmpCvmOutPath, packet, skin, residue, absorption } = input;

  if (!isFiniteNumber(cvm.alignment_index)) {
    fail("cvm.alignment_index", tmpCvmOutPath);
  }

  const phiRaw = cvm.final?.phi as Record<string, unknown> | undefined;
  if (!phiRaw || typeof phiRaw !== "object") {
    fail("cvm.final.phi", tmpCvmOutPath);
  }
  const phi = phiRaw as Record<string, unknown>;

  const required = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"];
  const keys = Object.keys(phi);
  const missing = required.filter((k) => !(k in phi));
  const extras = keys.filter((k) => !required.includes(k));
  if (missing.length > 0 || extras.length > 0) {
    fail("cvm.final.phi.keys", tmpCvmOutPath, `missing=${missing.join(",")} extras=${extras.join(",")}`);
  }

  for (const k of required) {
    if (!isFiniteNumber(phi[k])) {
      fail(`cvm.final.phi.${k}`, tmpCvmOutPath);
    }
  }

  const tmpOut = readJson<CVMOut>(tmpCvmOutPath, (null as unknown) as CVMOut);
  if (!isFiniteNumber(tmpOut.iters)) {
    fail("tmp_cvm_out.iters", tmpCvmOutPath);
  }
  if (!isFiniteNumber(tmpOut.alignment_index)) {
    fail("tmp_cvm_out.alignment_index", tmpCvmOutPath);
  }

  const cvmTrace = packet.trace.find((t) => t.step === "cvm") as {
    info?: { iters?: unknown };
  } | undefined;
  const packetIters = cvmTrace?.info?.iters;
  if (!isFiniteNumber(packetIters)) {
    fail("packet.trace.cvm.iters", input.packetPath);
  }

  if (tmpOut.iters !== packetIters || tmpOut.iters !== skin.iters) {
    fail("iters propagation", input.packetPath, `tmp=${tmpOut.iters} packet=${packetIters} skin=${skin.iters}`);
  }

  if (Math.abs(tmpOut.alignment_index - skin.alignment_index) > 1e-6) {
    fail("alignment_index propagation", input.skinPath, `tmp=${tmpOut.alignment_index} skin=${skin.alignment_index}`);
  }

  for (const k of required) {
    const a = absorption[k as keyof Vector5];
    const r = residue.residue_vector[k as keyof Vector5];
    if (!isFiniteNumber(a) || a < 0 || a > 1) {
      fail(`absorption_proxy.${k}`, input.residuePath);
    }
    if (!isFiniteNumber(r) || r < 0 || r > 1) {
      fail(`residue_vector.${k}`, input.residuePath);
    }
    const diff = Math.abs(r - (1 - a));
    if (diff > 1e-9) {
      fail(`residue_vector.${k}`, input.residuePath, `diff=${diff}`);
    }
  }
}

type PhaseGate = "thermal" | "entry" | "stable" | "anchored" | "sutured" | "near_identity";

function phaseFromScore(i: number): PhaseGate {
  if (i >= I_HORIZON) return "near_identity";
  if (i >= I_CRITICAL) return "sutured";
  if (i >= I_ANCHOR) return "anchored";
  if (i >= I_STABLE) return "stable";
  if (i >= I_ENTRY) return "entry";
  return "thermal";
}

/**
 * Filtre de Primalit? (Anti-R?sonance CT).
 * 0 = harmonique, 1 = forte densit? de longueurs premi?res
 */
function calculatePrimalDissonance(text: string): number {
  const segments = text
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .split(/\s+/)
    .map((s) => s.length)
    .filter((l) => l > 0);

  if (segments.length === 0) return 1.0;

  const isPrime = (n: number): boolean => {
    if (n < 2) return false;
    for (let i = 2, s = Math.sqrt(n); i <= s; i++) {
      if (n % i === 0) return false;
    }
    return true;
  };

  const primeCount = segments.filter(isPrime).length;
  const ratio = primeCount / segments.length;

  if (!Number.isFinite(ratio)) return 1.0;
  return clamp01(ratio);
}

/**
 * Dedup decision gate:
 * - ok only if >= I_CRITICAL (skin / suture)
 * - all other phases remain residue-side (but still logged + slot-addressed)
 */
function gateByScore(i: number): DedupDecision {
  const phase = phaseFromScore(i);

  if (i >= I_CRITICAL) {
    return {
      ok: true,
      reasons: [],
      details: {
        i,
        phase,
        thresholds: {
          I_ENTRY,
          I_STABLE,
          I_ANCHOR,
          I_CRITICAL,
          I_HORIZON
        }
      }
    };
  }

  const reasons: string[] = [];
  reasons.push(`alignment_index < ${I_CRITICAL}`);

  // Give explicit phase reason
  if (phase === "thermal") reasons.push(`below_entry(${I_ENTRY})`);
  else if (phase === "entry") reasons.push(`below_stable(${I_STABLE})`);
  else if (phase === "stable") reasons.push(`below_anchor(${I_ANCHOR})`);
  else if (phase === "anchored") reasons.push(`below_suture(${I_CRITICAL})`);

  return {
    ok: false,
    reasons,
    details: {
      i,
      phase,
      thresholds: {
        I_ENTRY,
        I_STABLE,
        I_ANCHOR,
        I_CRITICAL,
        I_HORIZON
      }
    }
  };
}

/**
 * CT projection: (0,+inf) -> (0,1) smooth (no hard clip-to-1).
 * log1p compression + ?-horizon (internal, then clamp to [0,1]).
 */
function project01_ct(x: number): number {
  if (!Number.isFinite(x)) return 0;
  const u = Math.max(0, x);

  const kappa = PI * PHI;           // CT scale
  const z = Math.log1p(u / kappa);  // ln-like compression
  const y = z / (z + PI);           // ?-horizon

  if (!Number.isFinite(y)) return 0;
  return clamp01(y);
}

function phiToAbsorption(phi: any): Vector5 {
  const get = (k: string) => (typeof phi?.[k] === "number" ? phi[k] : 0);
  return {
    PI: project01_ct(get("PI")),
    SQRT2: project01_ct(get("SQRT2")),
    SQRT3: project01_ct(get("SQRT3")),
    PHI: project01_ct(get("PHI")),
    LN5: project01_ct(get("LN5"))
  };
}

function absorptionToResidue(A: Vector5): Vector5 {
  return {
    PI: clamp01(1 - A.PI),
    SQRT2: clamp01(1 - A.SQRT2),
    SQRT3: clamp01(1 - A.SQRT3),
    PHI: clamp01(1 - A.PHI),
    LN5: clamp01(1 - A.LN5)
  };
}

function dominanceOf(v: Vector5): Mode5 {
  let best: Mode5 = "PI";
  let b = -1;
  const modes: Mode5[] = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"];
  for (const k of modes) {
    if (v[k] > b) {
      b = v[k];
      best = k;
    }
  }
  return best;
}

function ageBand(cycle_depth: number): ResidueAgeBand {
  if (cycle_depth < 2) return "fresh";
  if (cycle_depth < 5) return "mid";
  return "deep";
}

/**
 * Normalise un pool quelconque vers le contrat v5, sans casser les anciens JSON.
 */
function normalizePool(p: any): ResiduePool {
  const out: any = p && typeof p === "object" ? p : {};
  if (out.schema_version !== "ct.start1.residue_pool.v5") out.schema_version = "ct.start1.residue_pool.v5";
  if (typeof out.updated_utc !== "string") out.updated_utc = utcNow();
  if (!Array.isArray(out.clusters)) out.clusters = [];
  return out as ResiduePool;
}

export async function ingestFile(opts: { file: string; uri: string; root: string; cycle_depth: number; eps_son: number }) {
  if (!(opts.eps_son > 0)) throw new Error("eps_son doit ?tre > 0.");

  const raw = fs.readFileSync(opts.file, "utf8");
  const pid = packetId(opts.uri, raw);

  const packet: CausalPacket = {
    packet_id: pid,
    source: { uri: opts.uri, fetched_utc: utcNow() },
    raw,
    claims: atomizeClaims(raw, opts.uri, 32),
    status: "dirty",
    trace: [{ step: "ingest", utc: utcNow(), info: { file: opts.file, uri: opts.uri } }]
  };

  const claim = packet.claims[0];
  if (!claim) throw new Error("Aucun claim atomis?.");
  packet.trace.push({
    step: "atomize",
    utc: utcNow(),
    info: { claim_id: claim.id, claim_len: claim.text.length }
  });

  // 1) Anti-r?sonance (soft)
  const dissonance = calculatePrimalDissonance(claim.text);

  // 2) CTO -> vecteur
  const { vector, dominance } = transposeToVector(claim.text);
  packet.trace.push({
    step: "transpose",
    utc: utcNow(),
    info: { dominance, vector }
  });
  const csl = vectorToCSLText(vector);
  packet.trace.push({
    step: "csl",
    utc: utcNow(),
    info: { csl_bytes: Buffer.byteLength(csl, "utf8") }
  });

  // 3) CVM
  const cvm: CVMOut = runCvmMiniFromSiblingRepo(csl, opts.root, opts.eps_son);
  packet.trace.push({
    step: "cvm",
    utc: utcNow(),
    info: { converged: cvm.converged, iters: cvm.iters, i: cvm.alignment_index }
  });

  // --- CVM raw instrumentation (logs only) ---
  const phi_raw = (cvm.final?.phi || {}) as Record<string, unknown>;
  const phi_keys = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"] as const;
  const phi_vals = phi_keys.map((k) => safeNum(phi_raw[k], NaN));
  const finite = phi_vals.filter((v) => Number.isFinite(v)) as number[];
  const phi_min = finite.length ? Math.min(...finite) : NaN;
  const phi_max = finite.length ? Math.max(...finite) : NaN;

  const i_raw = safeNum(cvm.alignment_index, 0);

  console.log(
    `?? [CVM RAW] i_raw=${i_raw.toFixed(8)} phi_min=${Number.isFinite(phi_min) ? phi_min.toFixed(6) : "NaN"} phi_max=${
      Number.isFinite(phi_max) ? phi_max.toFixed(6) : "NaN"
    } eps_son=${String(opts.eps_son)}`
  );

  // 4) Score calibration (soft penalty, non-multiplicatif) + horizon clamp
  const gamma = 1 / (PI * PHI); // fixed CT penalty scale (stable)
  const i_penalized = Math.max(0, i_raw - gamma * dissonance);
  const final_i = clampHorizon(i_penalized);

  const phase = phaseFromScore(final_i);

  // 5) Build Skin object (always produced for audit, even if not sutured)
  const sid = skinId(vector);
  const skin: Skin = {
    skin_id: sid,
    vector,
    dominance,
    alignment_index: i_raw,
    converged: cvm.converged,
    iters: cvm.iters,
    cvm_trace_sample: (cvm.trace || []).slice(0, 16)
  };

  // 6) Residue (always produced for audit; pool persistence is gated)
  const A = phiToAbsorption(cvm.final?.phi || {});
  const R = absorptionToResidue(A);
  const rMode = dominanceOf(R);

  // Age-band: force "fresh" when below entry threshold (thermal / proto)
  const band: ResidueAgeBand = final_i < I_ENTRY ? "fresh" : ageBand(opts.cycle_depth);

  const rid = residueId({
    parent_skin_id: sid,
    residue_vector: R,
    cycle_depth: opts.cycle_depth,
    age_band: band,
    dominance: rMode
  });

  const residue: Residue = {
    residue_id: rid,
    parent_skin_id: sid,
    residue_vector: R,
    dominance: rMode,
    cycle_depth: opts.cycle_depth,
    age_band: band,
    absorption_proxy: A,
    raw_excerpt: claim.text.slice(0, 240)
  };

  packet.skin = skin;
  packet.residue = residue;

  const verdict = gateByScore(final_i);
  packet.status = verdict.ok ? "sutured" : "rejected";
  packet.trace.push({ step: "gate", utc: utcNow(), info: { ok: verdict.ok, reasons: verdict.reasons } });
  packet.trace.push({ step: "status", utc: utcNow(), info: { status: packet.status } });

  // 7) Pool persistence (always deposit residue per README contract)
  const outRoot = path.resolve(opts.root, "data", "out");
  ensureDir(path.join(outRoot, "packets"));
  ensureDir(path.join(outRoot, "skins"));
  ensureDir(path.join(outRoot, "residue"));
  const packetPath = path.join(outRoot, "packets", `${packet.packet_id}.packet.json`);
  const skinPath = path.join(outRoot, "skins", `${skin.skin_id}.skin.json`);
  const residuePath = path.join(outRoot, "residue", `${residue.residue_id}.residue.json`);
  const tmpCvmOutPath = path.join(outRoot, "logs", "tmp_cvm_out.json");
  assertInvariants({
    cvm,
    tmpCvmOutPath,
    packet,
    skin,
    residue,
    absorption: A,
    packetPath,
    skinPath,
    residuePath
  });
  writeJson(packetPath, packet);
  writeJson(skinPath, skin);
  writeJson(residuePath, residue);
  ensureDir(path.join(outRoot, "pools"));
  const poolPath = path.join(outRoot, "pools", "residue_pool.json");
  const loaded = readJson<any>(poolPath, newPool() as any);
  const pool = normalizePool(loaded);

  const dep = depositResidue(pool as any, residue.residue_id, residue.dominance, residue.age_band, residue.residue_vector);
  (dep.pool as any).schema_version = "ct.start1.residue_pool.v5";
  (dep.pool as any).updated_utc = utcNow();

  writeJson(poolPath, dep.pool);

  const attractor_id = dep.cluster?.attractor_id ?? null;
  const approach_velocity = dep.cluster?.approach_velocity ?? null;

  const logLine = {
    kind: "ingest",
    packet_id: packet.packet_id,
    status: packet.status,

    // Core score outputs
    alignment_index: final_i,
    phase_gate: phase,

    // Thresholds (explicit + auditable)
    thresholds: {
      I_ENTRY,
      I_STABLE,
      I_ANCHOR,
      I_CRITICAL,
      I_HORIZON
    },

    // Anti-resonance / penalties
    dissonance_score: dissonance,
    penalty_gamma: gamma,

    // CVM raw instrumentation
    cvm_alignment_raw: i_raw,
    cvm_phi_min: Number.isFinite(phi_min) ? phi_min : null,
    cvm_phi_max: Number.isFinite(phi_max) ? phi_max : null,

    // Slot addressing
    attractor_id,
    approach_velocity,

    // Near-identity flag (replaces old 0.99975 logic)
    near_identity: final_i >= I_HORIZON,
    residue_deposited: true
  };

  console.log(`\n?? [SPECTRE CT - SLOT ${String(logLine.attractor_id)}]`);
  console.log(
    `?? i=${logLine.alignment_index.toFixed(6)} | phase=${logLine.phase_gate} | i_raw=${logLine.cvm_alignment_raw.toFixed(6)} | dissonance=${logLine.dissonance_score.toFixed(4)}`
  );
  console.log(`??? status=${logLine.status} | near_identity=${String(logLine.near_identity)}`);

  ensureDir(path.join(outRoot, "logs"));
  writeText(path.join(outRoot, "logs", `${packet.packet_id}.log.json`), canonicalize(logLine));

  return logLine;
}

