// C:\CT\github\ct-cvm-mini\src\engine.ts
//
// Engine "vrai": pas de stub. Pas de runCVM(v)=>....
// Ce fichier expose :
//  - CT_CONSTANTS (calculées, pas hardcodées)
//  - runCVM(prog) : exécute la relaxation et retourne un CVMResult canonique
//

import type { CSLProgram, CVMResult, NodeId, Phi5 } from "./types.js";

export const CT_CONSTANTS = {
  PI: Math.PI,
  PHI: (1 + Math.sqrt(5)) / 2,
  SQRT2: Math.sqrt(2),
  SQRT3: Math.sqrt(3),
  LN5: Math.log(5),
} as const;

function clamp(x: number, a: number, b: number): number {
  return Math.max(a, Math.min(b, x));
}

export function runCVM(prog: CSLProgram): CVMResult {
  const { alpha, clamp: clp, steps, tol } = prog.params;

  // Champ phi par nœud
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
      // nœuds pinned : invariants
      if (node.pinned !== undefined) return;

      // Couplage par arêtes
      const neighbors = prog.edges.filter((e) => e.a === id || e.b === id);

      let coupling = 0;
      for (const e of neighbors) {
        const other = e.a === id ? e.b : e.a;
        coupling += e.w * (phi.get(other) ?? 0);
      }

      const avg =
        neighbors.length > 0 ? coupling / neighbors.length : (phi.get(id) ?? 0);

      // Flots dirigés
      let flows = 0;
      for (const f of prog.flows) {
        if (f.to === id) flows += f.k * (phi.get(f.from) ?? 0);
        if (f.from === id) flows -= f.k * (phi.get(id) ?? 0);
      }

      const current = phi.get(id) ?? 0;

      // Dynamique: décroissance + injection par (avg + flows)
      const next = (1 - node.decay) * current + alpha * (avg + flows);

      // Clamp: stabilité numérique
      const finalV = clamp(next, -clp, clp);

      maxDelta = Math.max(maxDelta, Math.abs(finalV - current));
      nextPhi.set(id, finalV);
    });

    // Commit
    nextPhi.forEach((v, k) => phi.set(k, v));

    trace.push({ iter: iters, max_delta: maxDelta, energy: 0 });

    if (maxDelta < tol) {
      converged = true;
      break;
    }
  }

  // i = métrique de convergence (pas vérité)
  // bornée et monotone: mieux si convergence + peu d'iters
  const alignment_index = converged
    ? 0.95 + 0.05 * (1 - iters / steps)
    : 0.80;

  // IMPORTANT: sortie canonique Start-1 attend final.phi.{PI,SQRT2,SQRT3,PHI,LN5}
  // On lit les nœuds si présents, sinon 0.
  const phi5: Phi5 = {
    PI: phi.get("PI") ?? 0,
    SQRT2: phi.get("SQRT2") ?? 0,
    SQRT3: phi.get("SQRT3") ?? 0,
    PHI: phi.get("PHI") ?? 0,
    LN5: phi.get("LN5") ?? 0,
  };

  // Sanity: pas de NaN/Inf
  (Object.keys(phi5) as (keyof Phi5)[]).forEach((k) => {
    if (!Number.isFinite(phi5[k])) phi5[k] = 0;
  });

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
