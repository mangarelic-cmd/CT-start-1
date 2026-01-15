// File: src/types.ts
// Start-1 core types — compatible with CURRENT modules + tolerant to legacy residue_pool.json
// Rules:
// - Compile with residue_pool.ts / round.ts / pipeline.ts
// - Avoid "any": use unknown
// - Keep legacy aliases OPTIONAL so old JSON can be read + normalized

export type Mode5 = "PI" | "SQRT2" | "SQRT3" | "PHI" | "LN5";
export type Vector5 = Record<Mode5, number>;
export type DupPhase = "none" | "symmetry" | "correction" | "expansion" | "dissipation" | "cycle";

// --- CVM output (ct-cvm-mini bridge) ---
export type CVMOut = {
  converged: boolean;
  iters: number;
  alignment_index: number;
  final: { phi: Vector5 };
  graph: unknown;
  trace: Array<{ iter: number; max_delta: number; energy: number }>;
};

// --- Atomized claim units (Start-1 does NOT judge truth) ---
export type Claim = {
  id: string;
  text: string;
  utc?: string;
  source_locator?: string;
};

// --- Skin = stable canonical representative ---
export type Skin = {
  skin_id: string;
  vector: Vector5;
  dominance: Mode5;
  alignment_index: number;
  converged: boolean;
  iters: number;
  cvm_trace_sample: Array<{ iter: number; max_delta: number; energy: number }>;
};

// --- Residue = non-fusable matter preserved for future rounds ---
export type ResidueAgeBand = "fresh" | "mid" | "deep";

export type Residue = {
  residue_id: string;
  parent_skin_id: string;

  residue_vector: Vector5;
  dominance: Mode5;
  cycle_depth: number;
  age_band: ResidueAgeBand;

  absorption_proxy: Vector5;
  raw_excerpt?: string;
};

// --- Packet = append-only ingestion record ---
export type PacketStatus = "dirty" | "processed" | "sutured" | "rejected";

export type CausalPacket = {
  packet_id: string;
  source: { uri: string; fetched_utc: string };
  raw: string;
  claims: Claim[];

  skin?: Skin;
  residue?: Residue;

  status: PacketStatus;
  trace: Array<{ step: string; utc: string; info: unknown }>;
};

export type DedupDecision = {
  ok: boolean;
  reasons: string[];
  details?: unknown;
};

// --- Residue clustering (pool is live; reprocessed on events) ---
// CURRENT (v5) canonical fields used by residue_pool.ts:
export type ResidueCluster = {
  cluster_id: string;

  // compatibility locks (CURRENT)
  mode: Mode5;
  age_band: ResidueAgeBand;

  // representative state (CURRENT)
  representative: Vector5;
  representative_hash: string;

  // membership/audit (CURRENT)
  count: number;
  member_residue_ids: string[];

  // CT-1030 address + diagnostics (CURRENT)
  attractor_id: string | null; // "T1".."T118"
  d_son_current: number | null;
  d_son_min: number | null;
  approach_velocity: number | null;

  // stability/lineage (CURRENT)
  last_cycle_depth: number | null;
  stable_streak: number;
  law_candidate: boolean;

  // merge trace (OPTIONAL)
  last_dup_phase?: DupPhase;
  last_merge_sim?: number;
  last_merge_weight?: number;

  // --- Legacy aliases (OPTIONAL) for old JSON / older modules ---
  dominance?: Mode5;
  representative_vector?: Vector5;
  members?: string[];
  member_ids?: string[];
};

// ResiduePool: CURRENT newPool() writes schema_version + updated_utc,
// but OPTIONAL to tolerate older JSON.
export type ResiduePool = {
  schema_version?: "ct.start1.residue_pool.v5";
  updated_utc?: string;
  clusters: ResidueCluster[];
};
