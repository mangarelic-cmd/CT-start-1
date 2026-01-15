// File: src/attractor.ts
import type { Vector5 } from "./types.js";
import type { Slot118, Level4 } from "./slots_118.js";
import { SLOTS_118 } from "./slots_118.js";

/**
 * CT-1030 Attractor Mapping (addresses, not meanings)
 *
 * IMPORTANT:
 * - slots_118.ts defines pattern order as: (PHI, SQRT2, SQRT3, LN5, PI)
 * - This file MUST use the same order for projection math.
 */

const KEYS: Array<keyof Vector5> = ["PHI", "SQRT2", "SQRT3", "LN5", "PI"];
const EPS_TIE = 1e-12;

function R_total(r: Vector5): number {
  return r.PI + r.SQRT2 + r.SQRT3 + r.PHI + r.LN5;
}

function sonCoord(r: Vector5): Vector5 {
  const R = R_total(r);
  if (!(R > 0) || !Number.isFinite(R)) {
    return { PI: 0.2, SQRT2: 0.2, SQRT3: 0.2, PHI: 0.2, LN5: 0.2 };
  }
  return {
    PI: r.PI / R,
    SQRT2: r.SQRT2 / R,
    SQRT3: r.SQRT3 / R,
    PHI: r.PHI / R,
    LN5: r.LN5 / R
  };
}

function dist2(a: Vector5, b: Vector5): number {
  return (
    (a.PI - b.PI) ** 2 +
    (a.SQRT2 - b.SQRT2) ** 2 +
    (a.SQRT3 - b.SQRT3) ** 2 +
    (a.PHI - b.PHI) ** 2 +
    (a.LN5 - b.LN5) ** 2
  );
}

function d(a: Vector5, b: Vector5): number {
  return Math.sqrt(dist2(a, b));
}

type SolveCandidate = { proj: Vector5; dist: number };

function buildIdxs(pattern: [Level4, Level4, Level4, Level4, Level4]) {
  const idxs: Record<Level4, number[]> = { h: [], m: [], l: [], z: [] };
  for (let i = 0; i < 5; i++) idxs[pattern[i]].push(i);
  return idxs;
}

function solveQuantizedProjection(
  s: Vector5,
  pattern: [Level4, Level4, Level4, Level4, Level4]
): SolveCandidate {
  const idxs = buildIdxs(pattern);
  const sArr = KEYS.map((k) => s[k]);

  const ch = idxs.h.length;
  const cm = idxs.m.length;
  const cl = idxs.l.length;

  if (ch + cm + cl <= 0) return { proj: s, dist: Number.POSITIVE_INFINITY };

  const Sh = idxs.h.reduce((acc, i) => acc + sArr[i], 0);
  const Sm = idxs.m.reduce((acc, i) => acc + sArr[i], 0);
  const Sl = idxs.l.reduce((acc, i) => acc + sArr[i], 0);

  type Part = { groups: Array<Array<"h" | "m" | "l">>; lFixedZero: boolean };

  const parts: Part[] = [
    { groups: [["h"], ["m"], ["l"]], lFixedZero: false },
    { groups: [["h", "m"], ["l"]], lFixedZero: false },
    { groups: [["h"], ["m", "l"]], lFixedZero: false },
    { groups: [["h", "m", "l"]], lFixedZero: false },
    { groups: [["h"], ["m"]], lFixedZero: true },
    { groups: [["h", "m"]], lFixedZero: true }
  ];

  const countOf = (lv: "h" | "m" | "l") => (lv === "h" ? ch : lv === "m" ? cm : cl);
  const sumOf = (lv: "h" | "m" | "l") => (lv === "h" ? Sh : lv === "m" ? Sm : Sl);

  let best: SolveCandidate | null = null;

  for (const part of parts) {
    // groups must have positive count
    let ok = true;
    for (const g of part.groups) {
      const c = g.reduce((acc, lv) => acc + countOf(lv), 0);
      if (c <= 0) {
        ok = false;
        break;
      }
    }
    if (!ok) continue;

    const Ctot = part.groups.reduce((acc, g) => acc + g.reduce((x, lv) => x + countOf(lv), 0), 0);
    const Stot = part.groups.reduce((acc, g) => acc + g.reduce((x, lv) => x + sumOf(lv), 0), 0);

    if (!(Ctot > 0) || !Number.isFinite(Stot)) continue;

    const t = (Stot - 1.0) / Ctot;

    const vg = part.groups.map((g) => {
      const c = g.reduce((x, lv) => x + countOf(lv), 0);
      const S = g.reduce((x, lv) => x + sumOf(lv), 0);
      return S / c - t;
    });

    // feasibility: nonneg + monotone group order
    let feasible = true;
    for (let i = 0; i < vg.length; i++) {
      if (!Number.isFinite(vg[i]) || vg[i] < -1e-12) {
        feasible = false;
        break;
      }
      if (i > 0 && vg[i - 1] + 1e-12 < vg[i]) {
        feasible = false;
        break;
      }
    }
    if (!feasible) continue;

    let vh = 0,
      vm = 0,
      vl = 0;

    const setLevels = (levels: Array<"h" | "m" | "l">, value: number) => {
      for (const lv of levels) {
        if (lv === "h") vh = value;
        if (lv === "m") vm = value;
        if (lv === "l") vl = value;
      }
    };

    for (let gi = 0; gi < part.groups.length; gi++) setLevels(part.groups[gi], vg[gi]);
    if (part.lFixedZero) vl = 0;

    if (vh + 1e-12 < vm || vm + 1e-12 < vl || vl < -1e-12) continue;

    vh = Math.max(0, vh);
    vm = Math.max(0, vm);
    vl = Math.max(0, vl);

    const projArr = [0, 0, 0, 0, 0];
    for (const i of idxs.h) projArr[i] = vh;
    for (const i of idxs.m) projArr[i] = vm;
    for (const i of idxs.l) projArr[i] = vl;
    for (const i of idxs.z) projArr[i] = 0;

    const sum = projArr.reduce((acc, v) => acc + v, 0);
    if (!Number.isFinite(sum) || Math.abs(sum - 1.0) > 1e-7) continue;

    // Map projArr back to Vector5 using KEYS order (PHI,SQRT2,SQRT3,LN5,PI)
    const proj: Vector5 = { PI: 0, SQRT2: 0, SQRT3: 0, PHI: 0, LN5: 0 };
    for (let i = 0; i < 5; i++) {
      const k = KEYS[i];
      proj[k] = projArr[i];
    }

    const dist = d(s, proj);
    if (!Number.isFinite(dist)) continue;

    const cand: SolveCandidate = { proj, dist };
    if (!best || cand.dist < best.dist) best = cand;
  }

  if (!best) return { proj: s, dist: Number.POSITIVE_INFINITY };
  return best;
}

export type AttractorHit = {
  slot_id: string; // "T1".."T118"
  d_son: number;
  projected: Vector5;
  slot: Slot118;
};

function betterHit(a: AttractorHit | null, b: AttractorHit): boolean {
  if (!a) return true;
  if (b.d_son + EPS_TIE < a.d_son) return true;
  if (a.d_son + EPS_TIE < b.d_son) return false;
  return b.slot.idx < a.slot.idx;
}

export function nearestAttractorFromResidue(residue: Vector5): AttractorHit {
  const s = sonCoord(residue);
  let best: AttractorHit | null = null;

  for (const slot of SLOTS_118) {
    const sol = solveQuantizedProjection(s, slot.pattern);
    const hit: AttractorHit = {
      slot_id: slot.id,
      d_son: sol.dist,
      projected: sol.proj,
      slot
    };
    if (betterHit(best, hit)) best = hit;
  }

  if (!best) throw new Error("No slots loaded.");
  return best;
}
