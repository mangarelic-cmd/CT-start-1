import type { CSLProgram } from "./types.js";

type KV = { k: string; v: string };

const parseKeyEq = (t: string): KV | null => {
  const m = t.match(/^([a-zA-Z_][a-zA-Z0-9_]*)=(.+)$/);
  return m ? { k: m[1], v: m[2] } : null;
};

export function parseCSL(text: string): CSLProgram {
  const prog: CSLProgram = {
    params: { alpha: 0.18, clamp: 4.0, steps: 2000, tol: 1e-6 },
    nodes: new Map(),
    edges: [],
    flows: [],
  };

  const ensureNode = (id: string) => {
    if (!prog.nodes.has(id)) prog.nodes.set(id, { id, decay: 0.0 });
    return prog.nodes.get(id)!;
  };

  text.split(/\r?\n/).forEach((line) => {
    const l = line.trim();
    if (!l || l.startsWith("#")) return;

    const p = l.split(/\s+/);

    if (p[0] === "param") {
      // Format: param alpha 0.18   (pas de "=")
      const key = p[1];
      const val = Number(p[2]);
      if (!Number.isFinite(val)) throw new Error(`Bad param value: "${l}"`);

      if (key === "alpha") prog.params.alpha = val;
      else if (key === "tol") prog.params.tol = val;
      else if (key === "clamp") prog.params.clamp = val;
      else if (key === "steps") prog.params.steps = Math.max(1, Math.floor(val));
      else throw new Error(`Unknown param key: "${key}"`);

      return;
    }

    if (p[0] === "node") {
      // Format: node A
      ensureNode(p[1]);
      return;
    }

    if (p[0] === "edge") {
      // Format: edge A B w=1.0
      const e = { a: p[1], b: p[2], w: 1.0 };
      p.slice(3).forEach((t) => {
        const kv = parseKeyEq(t);
        if (kv?.k === "w") e.w = Number(kv.v);
      });
      ensureNode(e.a);
      ensureNode(e.b);
      prog.edges.push(e);
      return;
    }

    if (p[0] === "flow") {
      // Format: flow A -> B k=0.2
      const from = p[1];
      const arrow = p[2];
      const to = p[3];
      if (arrow !== "->") throw new Error(`Bad flow syntax: "${l}"`);

      let k = 0.2;
      p.slice(4).forEach((t) => {
        const kv = parseKeyEq(t);
        if (kv?.k === "k") k = Number(kv.v);
      });

      ensureNode(from);
      ensureNode(to);
      prog.flows.push({ from, to, k });
      return;
    }

    if (p[0] === "pin") {
      // Format: pin PI 1
      ensureNode(p[1]).pinned = Number(p[2]);
      return;
    }

    if (p[0] === "decay") {
      // Format: decay A 0.02
      ensureNode(p[1]).decay = Number(p[2]);
      return;
    }

    throw new Error(`Unknown CSL line: "${l}"`);
  });

  return prog;
}
