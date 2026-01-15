// File: src/round.ts
// Purpose: Start-1 round runner (event-driven).
// Dependency-safe with residue_pool.ts v5 + fsutil.ts + crypto.ts.

import path from "node:path";
import { canonicalize, utcNow } from "./crypto.js";
import { readJson, writeJson, writeText, ensureDir } from "./fsutil.js";
import type { ResiduePool } from "./types.js";
import { newPool, reduceToFixpoint } from "./residue_pool.js";

/**
 * Start-1 rule: rounds are event-driven.
 * "scope" is allowed only as operational batching label, not causal law.
 */
export function runRound(opts: {
  root: string;
  cycle_depth: number;
  eps_son: number;
  scope: string;
}) {
  if (!(opts.eps_son > 0)) {
    throw new Error("eps_son doit être > 0 (CT: pas de valeur par défaut).");
  }

  const outRoot = path.resolve(opts.root, "data", "out");
  const poolsDir = path.join(outRoot, "pools");
  const logsDir = path.join(outRoot, "logs");
  ensureDir(poolsDir);
  ensureDir(logsDir);

  const poolPath = path.join(poolsDir, "residue_pool.json");
  const pool = readJson<ResiduePool>(poolPath, newPool());

  const res = reduceToFixpoint(pool, opts.cycle_depth, opts.eps_son, opts.scope);
  writeJson(poolPath, res.pool);

  const logLine = {
    kind: "round",
    utc: utcNow(),
    scope: opts.scope,
    cycle_depth: opts.cycle_depth,
    eps_son: opts.eps_son,
    merges: res.note.merges,
    clusters_after: res.pool.clusters.length,
    trace_sample: (res.note.trace || []).slice(0, 50)
  };

  const logName = `round_${opts.scope}_cycle_${opts.cycle_depth}_${Date.now()}.log.json`;
  writeText(path.join(logsDir, logName), canonicalize(logLine));

  return logLine;
}
