// File: src/residue_pool.ts
import { sha256, canonicalize, utcNow } from "./crypto.js";
import type {
  ResiduePool,
  ResidueCluster,
  Vector5,
  Mode5,
  ResidueAgeBand,
  DupPhase
} from "./types.js";
import { nearestAttractorFromResidue } from "./attractor.js";

function clamp01(x: number) {
  return Math.max(0, Math.min(1, x));
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function similarityFromDSon(d: number): number {
  const dMax = Math.SQRT2;
  const ratio = dMax > 0 ? d / dMax : 1;
  return clamp01(1 - ratio);
}

function dupPhaseFromSim(sim: number): DupPhase {
  if (sim < 0.61) return "none";
  if (sim < 0.66) return "symmetry";
  if (sim < 0.78) return "correction";
  if (sim < 0.87) return "expansion";
  if (sim < 0.946) return "dissipation";
  return "cycle";
}

function residueWeightFromSim(sim: number): number | null {
  if (sim < 0.61) return null;
  if (sim >= 0.946) return 0;
  if (sim >= 0.87) {
    return lerp(0.25, 0, (sim - 0.87) / (0.946 - 0.87));
  }
  if (sim >= 0.78) {
    return lerp(0.5, 0.25, (sim - 0.78) / (0.87 - 0.78));
  }
  if (sim >= 0.66) {
    return lerp(0.75, 0.5, (sim - 0.66) / (0.78 - 0.66));
  }
  return lerp(1.0, 0.75, (sim - 0.61) / (0.66 - 0.61));
}

function cleanVector(v: Vector5): Vector5 {
  return {
    PI: clamp01(v.PI),
    SQRT2: clamp01(v.SQRT2),
    SQRT3: clamp01(v.SQRT3),
    PHI: clamp01(v.PHI),
    LN5: clamp01(v.LN5)
  };
}

function repHash(v: Vector5): string {
  return sha256(canonicalize(cleanVector(v)));
}

function sumR(v: Vector5): number {
  return v.PI + v.SQRT2 + v.SQRT3 + v.PHI + v.LN5;
}

function sonCoord(v: Vector5): Vector5 {
  const r = sumR(v);
  if (r > 0) {
    return {
      PI: v.PI / r,
      SQRT2: v.SQRT2 / r,
      SQRT3: v.SQRT3 / r,
      PHI: v.PHI / r,
      LN5: v.LN5 / r
    };
  }
  return { PI: 0.2, SQRT2: 0.2, SQRT3: 0.2, PHI: 0.2, LN5: 0.2 };
}

function sonDist(a: Vector5, b: Vector5): number {
  const sa = sonCoord(a);
  const sb = sonCoord(b);
  const d1 = sa.PI - sb.PI;
  const d2 = sa.SQRT2 - sb.SQRT2;
  const d3 = sa.SQRT3 - sb.SQRT3;
  const d4 = sa.PHI - sb.PHI;
  const d5 = sa.LN5 - sb.LN5;
  return Math.sqrt(d1 * d1 + d2 * d2 + d3 * d3 + d4 * d4 + d5 * d5);
}

function mergeMin(a: Vector5, b: Vector5): Vector5 {
  return {
    PI: Math.min(a.PI, b.PI),
    SQRT2: Math.min(a.SQRT2, b.SQRT2),
    SQRT3: Math.min(a.SQRT3, b.SQRT3),
    PHI: Math.min(a.PHI, b.PHI),
    LN5: Math.min(a.LN5, b.LN5)
  };
}

function mergeWeighted(a: Vector5, b: Vector5, w: number): Vector5 {
  const rMin = mergeMin(a, b);
  const rMax = {
    PI: Math.max(a.PI, b.PI),
    SQRT2: Math.max(a.SQRT2, b.SQRT2),
    SQRT3: Math.max(a.SQRT3, b.SQRT3),
    PHI: Math.max(a.PHI, b.PHI),
    LN5: Math.max(a.LN5, b.LN5)
  };
  return {
    PI: rMin.PI + w * Math.abs(rMax.PI - rMin.PI),
    SQRT2: rMin.SQRT2 + w * Math.abs(rMax.SQRT2 - rMin.SQRT2),
    SQRT3: rMin.SQRT3 + w * Math.abs(rMax.SQRT3 - rMin.SQRT3),
    PHI: rMin.PHI + w * Math.abs(rMax.PHI - rMin.PHI),
    LN5: rMin.LN5 + w * Math.abs(rMax.LN5 - rMin.LN5)
  };
}

export function newPool(): ResiduePool {
  return {
    schema_version: "ct.start1.residue_pool.v5",
    updated_utc: utcNow(),
    clusters: []
  };
}

export function depositResidue(
  pool: ResiduePool,
  residue_id: string,
  dominance: Mode5,
  age_band: ResidueAgeBand,
  residue_vector: Vector5
): { pool: ResiduePool; cluster: ResidueCluster; note: string } {
  if (!pool || typeof pool !== "object") pool = newPool();
  if (pool.schema_version !== "ct.start1.residue_pool.v5") pool.schema_version = "ct.start1.residue_pool.v5";
  if (!Array.isArray(pool.clusters)) pool.clusters = [];
  pool.updated_utc = utcNow();

  const v = cleanVector(residue_vector);
  const rh = repHash(v);

  const hit = nearestAttractorFromResidue(v);
  const attractor_id = hit.slot_id;
  const d_son_current = hit.d_son;
  const approach_velocity = 0;

  const created_utc = utcNow();
  const cluster_id = sha256(
    canonicalize({
      kind: "cluster",
      residue_id,
      representative_hash: rh,
      created_utc
    })
  ).slice(0, 16);

  const cluster: ResidueCluster = {
    cluster_id,

    mode: dominance,
    age_band,

    representative: v,
    representative_hash: rh,

    count: 1,
    member_residue_ids: [residue_id],

    attractor_id,
    d_son_current,
    d_son_min: d_son_current,
    approach_velocity,

    last_cycle_depth: null,
    stable_streak: 0,

    law_candidate: false,

    last_dup_phase: "none",
    last_merge_sim: undefined,
    last_merge_weight: undefined
  };

  pool.clusters.push(cluster);

  return { pool, cluster, note: "monad_deposited_ct1030_mapped" };
}

export function reduceToFixpoint(
  pool: ResiduePool,
  cycle_depth: number,
  eps_son: number,
  scope: string
): { pool: ResiduePool; note: { merges: number; trace: unknown[] } } {
  if (cycle_depth < 0) {
    throw new Error("cycle_depth doit ?tre >= 0.");
  }
  if (!pool || typeof pool !== "object") pool = newPool();
  if (pool.schema_version !== "ct.start1.residue_pool.v5") pool.schema_version = "ct.start1.residue_pool.v5";
  if (!Array.isArray(pool.clusters)) pool.clusters = [];
  pool.updated_utc = utcNow();

  for (const c of pool.clusters) {
    const last = c.last_cycle_depth;
    if (typeof last === "number" && cycle_depth > last) {
      c.stable_streak = (c.stable_streak ?? 0) + 1;
    }
    c.last_cycle_depth = cycle_depth;
    c.law_candidate = c.age_band === "deep" && c.stable_streak >= 3;
  }

  const trace: unknown[] = [];
  let merges = 0;
  const max_passes = 34;

  for (let pass = 0; pass < max_passes; pass++) {
    let best: { i: number; j: number; d: number; key: string } | null = null;

    for (let i = 0; i < pool.clusters.length; i++) {
      for (let j = i + 1; j < pool.clusters.length; j++) {
        const a = pool.clusters[i];
        const b = pool.clusters[j];
        if (a.mode !== b.mode || a.age_band !== b.age_band) continue;
        const d = sonDist(a.representative, b.representative);
        const key = [a.cluster_id, b.cluster_id].sort().join("|");
        if (
          !best ||
          d < best.d ||
          (d === best.d && key < best.key)
        ) {
          best = { i, j, d, key };
        }
      }
    }

    if (!best) break;

    const a = pool.clusters[best.i];
    const b = pool.clusters[best.j];
    const sim = similarityFromDSon(best.d);
    const w = residueWeightFromSim(sim);
    if (w === null) {
      trace.push({
        step: "blocked",
        pass,
        blocked_reason: "w_null",
        d_son: best.d,
        sim,
        eps_son
      });
      break;
    }
    const phase = dupPhaseFromSim(sim);
    const r_after = cleanVector(mergeWeighted(a.representative, b.representative, w));
    const r_before_a = sumR(a.representative);
    const r_before_b = sumR(b.representative);
    const r_after_sum = sumR(r_after);
    const max_before = Math.max(r_before_a, r_before_b);

    if (best.d <= eps_son && r_after_sum < max_before) {
      const merged_hash = repHash(r_after);
      const merged_id = sha256(
        canonicalize({
          kind: "cluster-merge",
          a: a.cluster_id,
          b: b.cluster_id,
          representative_hash: merged_hash
        })
      ).slice(0, 16);

      const hit = nearestAttractorFromResidue(r_after);

      const ordered = [a, b].sort((x, y) => (x.cluster_id < y.cluster_id ? -1 : x.cluster_id > y.cluster_id ? 1 : 0));
      const merged_members = [...ordered[0].member_residue_ids, ...ordered[1].member_residue_ids];

      const merged: ResidueCluster = {
        cluster_id: merged_id,
        mode: a.mode,
        age_band: a.age_band,
        representative: r_after,
        representative_hash: merged_hash,
        count: a.count + b.count,
        member_residue_ids: merged_members,
        attractor_id: hit.slot_id,
        d_son_current: hit.d_son,
        d_son_min: hit.d_son,
        approach_velocity: 0,
        last_cycle_depth: cycle_depth,
        stable_streak: 0,
        law_candidate: false,
        last_dup_phase: phase,
        last_merge_sim: sim,
        last_merge_weight: w
      };

      const idxA = Math.max(best.i, best.j);
      const idxB = Math.min(best.i, best.j);
      pool.clusters.splice(idxA, 1);
      pool.clusters.splice(idxB, 1);
      pool.clusters.push(merged);

      merges++;
      trace.push({
        step: "merge",
        pass,
        a: a.cluster_id,
        b: b.cluster_id,
        d_son: best.d,
        phase,
        sim,
        w,
        r_before_a,
        r_before_b,
        r_after: r_after_sum,
        eps_son,
        merged_id
      });
    } else {
      trace.push({
        step: "blocked",
        pass,
        blocked_reason: best.d > eps_son ? "d_gt_eps" : "dissipation_not_decreasing",
        d_son: best.d,
        sim,
        w,
        r_before_a,
        r_before_b,
        r_after: r_after_sum,
        eps_son
      });
      break;
    }
  }

  if (merges === 0) {
    trace.push({
      step: "noop",
      scope,
      cycle_depth,
      eps_son,
      clusters: pool.clusters.length
    });
  }

  return { pool, note: { merges, trace } };
}

