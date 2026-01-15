// File: src/dedup.ts
// Purpose: Deterministic IDs based on canonicalized payloads.

import { sha256, canonicalize } from "./crypto.js";
import type { Vector5, Mode5, ResidueAgeBand } from "./types.js";

export function packetId(uri: string, raw: string): string {
  // Stable ID across runs
  return sha256(canonicalize({ kind: "packet", uri, raw }));
}

export function skinId(v: Vector5): string {
  return sha256(canonicalize({ kind: "skin", v }));
}

export function residueId(x: {
  parent_skin_id: string;
  residue_vector: Vector5;
  cycle_depth: number;
  age_band: ResidueAgeBand;
  dominance: Mode5;
}): string {
  return sha256(canonicalize({ kind: "residue", ...x }));
}
