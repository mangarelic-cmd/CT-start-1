// File: src/slots_118.ts
// Purpose: CT-1030 Slot table (T1..T118) with canonical shell indexing + canonical pattern order.
// Contract:
// - Slot IDs are exactly "T1".."T118" and match idx
// - shell is computed ONLY from idx using CT-1030 mapping
// - pattern order is CANONICAL: (PHI, SQRT2, SQRT3, LN5, PI)
// - T4 / T5 are forced to CT-1030 exact definitions (mode+pattern+label)
// - deterministic, dependency-safe (pure data + validation)

import type { Mode5 } from "./types.js";

export type Level4 = "h" | "m" | "l" | "z";

export type Slot118 = {
  id: string;
  idx: number;
  mode: Mode5;
  shell: number; // forced by fixSlot(idx)
  // IMPORTANT (1030): (PHI, SQRT2, SQRT3, LN5, PI)
  pattern: [Level4, Level4, Level4, Level4, Level4];
  label: string;
};

// Helper: convert old pattern order (PI,SQRT2,SQRT3,PHI,LN5) -> new (PHI,SQRT2,SQRT3,LN5,PI)
function P(old: [Level4, Level4, Level4, Level4, Level4]): [Level4, Level4, Level4, Level4, Level4] {
  return [old[3], old[1], old[2], old[4], old[0]];
}

// CT-1030 canonical shell indexing:
// n=1 → T1–T5; n=2 → T6–T25; n=3 → T26–T50; n=4 → T51–T81; n=5 → T82–T118
function shellFromIdx(idx: number): number {
  if (idx >= 1 && idx <= 5) return 1;
  if (idx >= 6 && idx <= 25) return 2;
  if (idx >= 26 && idx <= 50) return 3;
  if (idx >= 51 && idx <= 81) return 4;
  if (idx >= 82 && idx <= 118) return 5;
  throw new Error(`slots_118: invalid slot idx: ${idx}`);
}

function enforceIdIdx(slot: { id: string; idx: number }) {
  const expected = `T${slot.idx}`;
  if (slot.id !== expected) {
    throw new Error(`slots_118: id/idx mismatch: got id=${slot.id} idx=${slot.idx} expected id=${expected}`);
  }
}

function fixSlot(raw: Slot118): Slot118 {
  enforceIdIdx(raw);

  // Force canonical shell from idx (plan CT-1030)
  const shell = shellFromIdx(raw.idx);

  // Force CT-1030 T4/T5 exactly (mode + pattern + label) in order (PHI,SQRT2,SQRT3,LN5,PI)
  // Plan: T4=(ln5,1) pattern (l,l,m,h,l) ; T5=(pi,1) pattern (l,l,l,m,h)
  if (raw.idx === 4) {
    return {
      ...raw,
      shell,
      mode: "LN5",
      pattern: ["l", "l", "m", "h", "l"],
      label: "G5 Causal  dissipation; negation "
    };
  }
  if (raw.idx === 5) {
    return {
      ...raw,
      shell,
      mode: "PI",
      pattern: ["l", "l", "l", "m", "h"],
      label: "G4 Causal  closure; identity "
    };
  }

  return { ...raw, shell };
}

// RAW: shell=0 everywhere; ONLY fixSlot decides shells.
const RAW_SLOTS_118: Slot118[] = [
  { id: "T1", idx: 1, mode: "PHI", shell: 0, pattern: P(["h","l","l","l","l"]), label: "G1 Causal  CT core; equality " },
  { id: "T2", idx: 2, mode: "SQRT2", shell: 0, pattern: P(["l","h","m","m","l"]), label: "G2 Causal  coupling; dyad invariance " },
  { id: "T3", idx: 3, mode: "SQRT3", shell: 0, pattern: P(["l","m","h","m","l"]), label: "G3 Causal  triad frame; boundary " },
  { id: "T4", idx: 4, mode: "PI", shell: 0, pattern: P(["h","l","m","l","l"]), label: "G4 Causal  closure; identity " },
  { id: "T5", idx: 5, mode: "LN5", shell: 0, pattern: P(["l","m","l","l","h"]), label: "G5 Causal  dissipation; negation " },

  { id: "T6", idx: 6, mode: "PHI", shell: 0, pattern: P(["h","m","l","l","l"]), label: "G1 Causal  shell growth; recursion " },
  { id: "T7", idx: 7, mode: "SQRT2", shell: 0, pattern: P(["m","h","m","l","l"]), label: "G2 Causal  shell coupling; dyad " },
  { id: "T8", idx: 8, mode: "SQRT3", shell: 0, pattern: P(["m","m","h","l","l"]), label: "G3 Causal  shell boundary; triad " },
  { id: "T9", idx: 9, mode: "PI", shell: 0, pattern: P(["h","m","m","l","l"]), label: "G4 Causal  shell closure; rotation " },
  { id: "T10", idx: 10, mode: "LN5", shell: 0, pattern: P(["m","m","l","l","h"]), label: "G5 Causal  shell dissipation; entropy " },

  { id: "T11", idx: 11, mode: "PHI", shell: 0, pattern: P(["h","m","m","l","l"]), label: "Causal  growth; higher shell " },
  { id: "T12", idx: 12, mode: "SQRT2", shell: 0, pattern: P(["m","h","m","m","l"]), label: "Causal  dyad; higher shell " },
  { id: "T13", idx: 13, mode: "SQRT3", shell: 0, pattern: P(["m","m","h","m","l"]), label: "Causal  boundary; higher shell " },
  { id: "T14", idx: 14, mode: "PI", shell: 0, pattern: P(["h","m","m","m","l"]), label: "Causal  closure; higher shell " },
  { id: "T15", idx: 15, mode: "LN5", shell: 0, pattern: P(["m","m","m","l","h"]), label: "Causal  dissipation; higher shell " },

  { id: "T16", idx: 16, mode: "PHI", shell: 0, pattern: P(["h","m","m","m","l"]), label: "Causal  growth; shell 4 " },
  { id: "T17", idx: 17, mode: "SQRT2", shell: 0, pattern: P(["m","h","m","m","m"]), label: "Causal  dyad; shell 4 " },
  { id: "T18", idx: 18, mode: "SQRT3", shell: 0, pattern: P(["m","m","h","m","m"]), label: "Causal  triad; shell 4 " },
  { id: "T19", idx: 19, mode: "PI", shell: 0, pattern: P(["h","m","m","m","m"]), label: "Causal  closure; shell 4 " },
  { id: "T20", idx: 20, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Causal  dissipation; shell 4 " },

  { id: "T21", idx: 21, mode: "PHI", shell: 0, pattern: P(["h","m","m","m","m"]), label: "Causal  growth; shell 5 " },
  { id: "T22", idx: 22, mode: "SQRT2", shell: 0, pattern: P(["m","h","m","m","m"]), label: "Causal  dyad; shell 5 " },
  { id: "T23", idx: 23, mode: "SQRT3", shell: 0, pattern: P(["m","m","h","m","m"]), label: "Causal  triad; shell 5 " },
  { id: "T24", idx: 24, mode: "PI", shell: 0, pattern: P(["h","m","m","m","m"]), label: "Causal  closure; shell 5 " },
  { id: "T25", idx: 25, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Causal  dissipation; shell 5 " },

  { id: "T26", idx: 26, mode: "PHI", shell: 0, pattern: P(["h","l","m","m","l"]), label: "Mixed  growth + dyad " },
  { id: "T27", idx: 27, mode: "SQRT2", shell: 0, pattern: P(["l","h","m","m","m"]), label: "Mixed  dyad + triad " },
  { id: "T28", idx: 28, mode: "SQRT3", shell: 0, pattern: P(["l","m","h","m","m"]), label: "Mixed  triad + closure " },
  { id: "T29", idx: 29, mode: "PI", shell: 0, pattern: P(["h","l","m","m","m"]), label: "Mixed  closure + dyad " },
  { id: "T30", idx: 30, mode: "LN5", shell: 0, pattern: P(["l","m","m","m","h"]), label: "Mixed  dissipation + structure " },

  { id: "T31", idx: 31, mode: "PHI", shell: 0, pattern: P(["h","m","m","m","l"]), label: "Mixed  growth; shell 2 " },
  { id: "T32", idx: 32, mode: "SQRT2", shell: 0, pattern: P(["m","h","m","m","l"]), label: "Mixed  dyad; shell 2 " },
  { id: "T33", idx: 33, mode: "SQRT3", shell: 0, pattern: P(["m","m","h","m","l"]), label: "Mixed  triad; shell 2 " },
  { id: "T34", idx: 34, mode: "PI", shell: 0, pattern: P(["h","m","m","m","l"]), label: "Mixed  closure; shell 2 " },
  { id: "T35", idx: 35, mode: "LN5", shell: 0, pattern: P(["m","m","m","l","h"]), label: "Mixed  dissipation; shell 2 " },

  { id: "T36", idx: 36, mode: "PHI", shell: 0, pattern: P(["h","m","m","m","l"]), label: "Mixed  growth; shell 3 " },
  { id: "T37", idx: 37, mode: "SQRT2", shell: 0, pattern: P(["m","h","m","m","m"]), label: "Mixed  dyad; shell 3 " },
  { id: "T38", idx: 38, mode: "SQRT3", shell: 0, pattern: P(["m","m","h","m","m"]), label: "Mixed  triad; shell 3 " },
  { id: "T39", idx: 39, mode: "PI", shell: 0, pattern: P(["h","m","m","m","m"]), label: "Mixed  closure; shell 3 " },
  { id: "T40", idx: 40, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Mixed  dissipation; shell 3 " },

  { id: "T41", idx: 41, mode: "PHI", shell: 0, pattern: P(["h","m","m","m","m"]), label: "Mixed  growth; shell 4 " },
  { id: "T42", idx: 42, mode: "SQRT2", shell: 0, pattern: P(["m","h","m","m","m"]), label: "Mixed  dyad; shell 4 " },
  { id: "T43", idx: 43, mode: "SQRT3", shell: 0, pattern: P(["m","m","h","m","m"]), label: "Mixed  triad; shell 4 " },
  { id: "T44", idx: 44, mode: "PI", shell: 0, pattern: P(["h","m","m","m","m"]), label: "Mixed  closure; shell 4 " },
  { id: "T45", idx: 45, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Mixed  dissipation; shell 4 " },

  { id: "T46", idx: 46, mode: "PHI", shell: 0, pattern: P(["h","m","m","m","m"]), label: "Mixed  growth; shell 5 " },
  { id: "T47", idx: 47, mode: "SQRT2", shell: 0, pattern: P(["m","h","m","m","m"]), label: "Mixed  dyad; shell 5 " },
  { id: "T48", idx: 48, mode: "SQRT3", shell: 0, pattern: P(["m","m","h","m","m"]), label: "Mixed  triad; shell 5 " },
  { id: "T49", idx: 49, mode: "PI", shell: 0, pattern: P(["h","m","m","m","m"]), label: "Mixed  closure; shell 5 " },
  { id: "T50", idx: 50, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Mixed  dissipation; shell 5 " },

  { id: "T51", idx: 51, mode: "PHI", shell: 0, pattern: P(["h","m","h","l","l"]), label: "Structured  growth + closure " },
  { id: "T52", idx: 52, mode: "SQRT2", shell: 0, pattern: P(["m","h","h","l","l"]), label: "Structured  dyad + triad " },
  { id: "T53", idx: 53, mode: "SQRT3", shell: 0, pattern: P(["m","h","h","l","l"]), label: "Structured  triad + dyad " },
  { id: "T54", idx: 54, mode: "PI", shell: 0, pattern: P(["h","m","h","l","l"]), label: "Structured  closure + growth " },
  { id: "T55", idx: 55, mode: "LN5", shell: 0, pattern: P(["m","m","m","l","h"]), label: "Structured  dissipation " },

  { id: "T56", idx: 56, mode: "PHI", shell: 0, pattern: P(["h","m","h","m","l"]), label: "Structured  growth; shell 2 " },
  { id: "T57", idx: 57, mode: "SQRT2", shell: 0, pattern: P(["m","h","h","m","l"]), label: "Structured  dyad; shell 2 " },
  { id: "T58", idx: 58, mode: "SQRT3", shell: 0, pattern: P(["m","h","h","m","l"]), label: "Structured  triad; shell 2 " },
  { id: "T59", idx: 59, mode: "PI", shell: 0, pattern: P(["h","m","h","m","l"]), label: "Structured  closure; shell 2 " },
  { id: "T60", idx: 60, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Structured  dissipation; shell 2 " },

  { id: "T61", idx: 61, mode: "PHI", shell: 0, pattern: P(["h","m","h","m","m"]), label: "Structured  growth; shell 3 " },
  { id: "T62", idx: 62, mode: "SQRT2", shell: 0, pattern: P(["m","h","h","m","m"]), label: "Structured  dyad; shell 3 " },
  { id: "T63", idx: 63, mode: "SQRT3", shell: 0, pattern: P(["m","h","h","m","m"]), label: "Structured  triad; shell 3 " },
  { id: "T64", idx: 64, mode: "PI", shell: 0, pattern: P(["h","m","h","m","m"]), label: "Structured  closure; shell 3 " },
  { id: "T65", idx: 65, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Structured  dissipation; shell 3 " },

  { id: "T66", idx: 66, mode: "PHI", shell: 0, pattern: P(["h","m","h","m","m"]), label: "Structured  growth; shell 4 " },
  { id: "T67", idx: 67, mode: "SQRT2", shell: 0, pattern: P(["m","h","h","m","m"]), label: "Structured  dyad; shell 4 " },
  { id: "T68", idx: 68, mode: "SQRT3", shell: 0, pattern: P(["m","h","h","m","m"]), label: "Structured  triad; shell 4 " },
  { id: "T69", idx: 69, mode: "PI", shell: 0, pattern: P(["h","m","h","m","m"]), label: "Structured  closure; shell 4 " },
  { id: "T70", idx: 70, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Structured  dissipation; shell 4 " },

  { id: "T71", idx: 71, mode: "PHI", shell: 0, pattern: P(["h","m","h","m","m"]), label: "Structured  growth; shell 5 " },
  { id: "T72", idx: 72, mode: "SQRT2", shell: 0, pattern: P(["m","h","h","m","m"]), label: "Structured  dyad; shell 5 " },
  { id: "T73", idx: 73, mode: "SQRT3", shell: 0, pattern: P(["m","h","h","m","m"]), label: "Structured  triad; shell 5 " },
  { id: "T74", idx: 74, mode: "PI", shell: 0, pattern: P(["h","m","h","m","m"]), label: "Structured  closure; shell 5 " },
  { id: "T75", idx: 75, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Structured  dissipation; shell 5 " },

  { id: "T76", idx: 76, mode: "PHI", shell: 0, pattern: P(["h","h","h","l","l"]), label: "Triple  growth (3 highs) " },
  { id: "T77", idx: 77, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","l","l"]), label: "Triple  dyad (3 highs) " },
  { id: "T78", idx: 78, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","l","l"]), label: "Triple  triad (3 highs) " },
  { id: "T79", idx: 79, mode: "PI", shell: 0, pattern: P(["h","h","h","l","l"]), label: "Triple  closure (3 highs) " },
  { id: "T80", idx: 80, mode: "LN5", shell: 0, pattern: P(["m","m","m","l","h"]), label: "Triple  dissipation " },

  { id: "T81", idx: 81, mode: "PHI", shell: 0, pattern: P(["h","h","h","m","l"]), label: "Triple  shell 2 " },
  { id: "T82", idx: 82, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","m","l"]), label: "Triple  dyad shell 2 " },
  { id: "T83", idx: 83, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","m","l"]), label: "Triple  triad shell 2 " },
  { id: "T84", idx: 84, mode: "PI", shell: 0, pattern: P(["h","h","h","m","l"]), label: "Triple  closure shell 2 " },
  { id: "T85", idx: 85, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Triple  dissipation shell 2 " },

  { id: "T86", idx: 86, mode: "PHI", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  shell 3 " },
  { id: "T87", idx: 87, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  dyad shell 3 " },
  { id: "T88", idx: 88, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  triad shell 3 " },
  { id: "T89", idx: 89, mode: "PI", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  closure shell 3 " },
  { id: "T90", idx: 90, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Triple  dissipation shell 3 " },

  { id: "T91", idx: 91, mode: "PHI", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  shell 4 " },
  { id: "T92", idx: 92, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  dyad shell 4 " },
  { id: "T93", idx: 93, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  triad shell 4 " },
  { id: "T94", idx: 94, mode: "PI", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  closure shell 4 " },
  { id: "T95", idx: 95, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Triple  dissipation shell 4 " },

  { id: "T96", idx: 96, mode: "PHI", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  shell 5 " },
  { id: "T97", idx: 97, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  dyad shell 5 " },
  { id: "T98", idx: 98, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  triad shell 5 " },
  { id: "T99", idx: 99, mode: "PI", shell: 0, pattern: P(["h","h","h","m","m"]), label: "Triple  closure shell 5 " },
  { id: "T100", idx: 100, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Triple  dissipation shell 5 " },

  { id: "T101", idx: 101, mode: "PHI", shell: 0, pattern: P(["h","h","h","h","l"]), label: "Dense  4 highs " },
  { id: "T102", idx: 102, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","h","l"]), label: "Dense  dyad 4 highs " },
  { id: "T103", idx: 103, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","h","l"]), label: "Dense  triad 4 highs " },
  { id: "T104", idx: 104, mode: "PI", shell: 0, pattern: P(["h","h","h","h","l"]), label: "Dense  closure 4 highs " },
  { id: "T105", idx: 105, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Dense  dissipation " },

  { id: "T106", idx: 106, mode: "PHI", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  shell 2 " },
  { id: "T107", idx: 107, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  dyad shell 2 " },
  { id: "T108", idx: 108, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  triad shell 2 " },
  { id: "T109", idx: 109, mode: "PI", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  closure shell 2 " },
  { id: "T110", idx: 110, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Dense  dissipation shell 2 " },

  { id: "T111", idx: 111, mode: "PHI", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  shell 3 " },
  { id: "T112", idx: 112, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  dyad shell 3 " },
  { id: "T113", idx: 113, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  triad shell 3 " },
  { id: "T114", idx: 114, mode: "PI", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  closure shell 3 " },
  { id: "T115", idx: 115, mode: "LN5", shell: 0, pattern: P(["m","m","m","m","h"]), label: "Dense  dissipation shell 3 " },

  { id: "T116", idx: 116, mode: "PHI", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  shell 4 " },
  { id: "T117", idx: 117, mode: "SQRT2", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  dyad shell 4 " },
  { id: "T118", idx: 118, mode: "SQRT3", shell: 0, pattern: P(["h","h","h","h","m"]), label: "Dense  triad shell 4 " }
];

// Export final, plan-locked
export const SLOTS_118: Slot118[] = RAW_SLOTS_118.map(fixSlot);

// ---------- module-level validation (fail fast, no silent drift) ----------
(function validateSlots(slots: Slot118[]) {
  if (slots.length !== 118) {
    throw new Error(`slots_118: expected 118 slots, got ${slots.length}`);
  }

  const seen = new Set<string>();
  for (const s of slots) {
    enforceIdIdx(s);
    if (seen.has(s.id)) throw new Error(`slots_118: duplicate id ${s.id}`);
    seen.add(s.id);

    const expectedShell = shellFromIdx(s.idx);
    if (s.shell !== expectedShell) {
      throw new Error(`slots_118: shell mismatch for ${s.id}: got ${s.shell} expected ${expectedShell}`);
    }

    if (!Array.isArray(s.pattern) || s.pattern.length !== 5) {
      throw new Error(`slots_118: pattern length invalid for ${s.id}`);
    }
  }

  // Explicit check: CT-1030 forced anchors
  const t4 = slots[3]; // idx=4
  const t5 = slots[4]; // idx=5
  if (t4.id !== "T4" || t4.mode !== "LN5" || t4.pattern.join(",") !== ["l","l","m","h","l"].join(",")) {
    throw new Error(`slots_118: T4 anchor not locked correctly`);
  }
  if (t5.id !== "T5" || t5.mode !== "PI" || t5.pattern.join(",") !== ["l","l","l","m","h"].join(",")) {
    throw new Error(`slots_118: T5 anchor not locked correctly`);
  }
})(SLOTS_118);
