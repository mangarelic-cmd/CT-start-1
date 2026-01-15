import type { CSLProgram, CVMResult, NodeId, Phi5 } from "./types.js";

const PHI_KEYS: (keyof Phi5)[] = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"];

function clamp(x: number, a: number, b: number) {
  return Math.max(a, Math.min(b, x));
}

export function runCVM(prog: CSLProgram): CVMResult {
  const { alpha, clamp: clp, steps, tol } = prog.params;

  const phi = new Map<NodeId, number>();
  prog.nodes.forEach((n, id) => phi.set(id, n.pinned ?? 0));

  const trace: CVMResult["trace"] = [];
  let converged = false;
  let iters = 0;

  for (let t = 0; t < steps; t++) {
    iters = t + 1;
    let maxDelta = 0;
    const nextPhi = new Map(phi);

    prog.nodes.forEach((node, id) => {
      if (node.pinned !== undefined) return;

      const neighbors = prog.edges.filter((e) => e.a === id || e.b === id);

      let coupling = 0;
      for (const e of neighbors) {
        const other = e.a === id ? e.b : e.a;
        coupling += e.w * (phi.get(other) ?? 0);
      }

      const avg =
        neighbors.length > 0 ? coupling / neighbors.length : (phi.get(id) ?? 0);

      let flows = 0;
      for (const f of prog.flows) {
        if (f.to === id) flows += f.k * (phi.get(f.from) ?? 0);
        if (f.from === id) flows -= f.k * (phi.get(id) ?? 0);
      }

      const current = phi.get(id) ?? 0;
      const next = (1 - node.decay) * current + alpha * (avg + flows);
      const finalV = clamp(next, -clp, clp);

      maxDelta = Math.max(maxDelta, Math.abs(finalV - current));
      nextPhi.set(id, finalV);
    });

    nextPhi.forEach((v, k) => phi.set(k, v));

    trace.push({ iter: iters, max_delta: maxDelta, energy: 0 });

    if (maxDelta < tol) {
      converged = true;
      break;
    }
  }

  // Index d’alignement = métrique de convergence (pas vérité)
  const alignment_index = converged
    ? 0.95 + 0.05 * (1 - iters / steps)
    : 0.80;

  // IMPORTANT : final.phi DOIT être Phi5 (PI,SQRT2,SQRT3,PHI,LN5)
  // On lit ces nœuds si présents, sinon 0.
  const phi5: Phi5 = {
    PI: phi.get("PI") ?? 0,
    SQRT2: phi.get("SQRT2") ?? 0,
    SQRT3: phi.get("SQRT3") ?? 0,
    PHI: phi.get("PHI") ?? 0,
    LN5: phi.get("LN5") ?? 0,
  };

  // Force : assure que ces IDs existent même si non déclarés dans CSL
  // (Start-1 exige ces clés)
  for (const k of PHI_KEYS) {
    if (!Number.isFinite(phi5[k])) phi5[k] = 0;
  }

  return {
    converged,
    iters,
    alignment_index,
    final: { phi: phi5 },
    graph: {
      nodes: Array.from(prog.nodes.values()),
      edges: prog.edges,
      flows: prog.flows,
    },
    trace,
  };
}
