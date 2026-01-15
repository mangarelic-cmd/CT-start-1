export type NodeId = string;

export const I_CRITICAL = 0.946 as const;

export type CSLParams = {
  alpha: number;
  clamp: number;
  steps: number;
  tol: number;
};

export type CSLNode = {
  id: NodeId;
  decay: number;
  pinned?: number;
};

export type CSLEdge = { a: NodeId; b: NodeId; w: number };
export type CSLFlow = { from: NodeId; to: NodeId; k: number };

export type CSLProgram = {
  params: CSLParams;
  nodes: Map<NodeId, CSLNode>;
  edges: CSLEdge[];
  flows: CSLFlow[];
};

export type Phi5 = {
  PI: number;
  SQRT2: number;
  SQRT3: number;
  PHI: number;
  LN5: number;
};

export type CVMTraceRow = { iter: number; max_delta: number; energy: number };

export type CVMResult = {
  converged: boolean;
  iters: number;
  alignment_index: number;
  final: { phi: Phi5 };
  graph: { nodes: CSLNode[]; edges: CSLEdge[]; flows: CSLFlow[] };
  trace: CVMTraceRow[];
};
