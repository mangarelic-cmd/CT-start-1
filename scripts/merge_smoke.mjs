import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();
const inbox = path.join(root, "data", "inbox");
const outPools = path.join(root, "data", "out", "pools");
const poolPath = path.join(outPools, "residue_pool.json");

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function writeFile(p, content) {
  ensureDir(path.dirname(p));
  fs.writeFileSync(p, content, "utf8");
}

function runNode(args) {
  const out = execFileSync("node", args, { encoding: "utf8" });
  return out;
}

function parseLastJson(text) {
  const lines = text.trimEnd().split(/\r?\n/);
  const starts = [];
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trimStart().startsWith("{")) starts.push(i);
  }
  for (let s = starts.length - 1; s >= 0; s--) {
    const jsonText = lines.slice(starts[s]).join("\n");
    try {
      return JSON.parse(jsonText);
    } catch {
      // keep trying earlier starts
    }
  }
  throw new Error("No JSON object found in output");
}

function sumR(v) {
  return v.PI + v.SQRT2 + v.SQRT3 + v.PHI + v.LN5;
}

function sonCoord(v) {
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

function sonDist(a, b) {
  const sa = sonCoord(a);
  const sb = sonCoord(b);
  const d1 = sa.PI - sb.PI;
  const d2 = sa.SQRT2 - sb.SQRT2;
  const d3 = sa.SQRT3 - sb.SQRT3;
  const d4 = sa.PHI - sb.PHI;
  const d5 = sa.LN5 - sb.LN5;
  return Math.sqrt(d1 * d1 + d2 * d2 + d3 * d3 + d4 * d4 + d5 * d5);
}

function mergeMin(a, b) {
  return {
    PI: Math.min(a.PI, b.PI),
    SQRT2: Math.min(a.SQRT2, b.SQRT2),
    SQRT3: Math.min(a.SQRT3, b.SQRT3),
    PHI: Math.min(a.PHI, b.PHI),
    LN5: Math.min(a.LN5, b.LN5)
  };
}

function printCandidates(clusters, eps) {
  const candidates = [];
  for (let i = 0; i < clusters.length; i++) {
    for (let j = i + 1; j < clusters.length; j++) {
      const a = clusters[i];
      const b = clusters[j];
      if (a.mode !== b.mode || a.age_band !== b.age_band) continue;
      const d = sonDist(a.representative, b.representative);
      const rBeforeA = sumR(a.representative);
      const rBeforeB = sumR(b.representative);
      const rAfter = sumR(mergeMin(a.representative, b.representative));
      const deltaC = Math.max(rBeforeA, rBeforeB) - rAfter;
      candidates.push({
        a: a.cluster_id,
        b: b.cluster_id,
        mode: a.mode,
        age_band: a.age_band,
        d_son: d,
        delta_c: deltaC
      });
    }
  }

  if (candidates.length === 0) {
    console.log("No compatible pairs (mode+age_band) in pool.");
    return;
  }

  candidates.sort((x, y) => {
    if (x.d_son !== y.d_son) return x.d_son - y.d_son;
    const keyX = [x.a, x.b].sort().join("|");
    const keyY = [y.a, y.b].sort().join("|");
    return keyX < keyY ? -1 : keyX > keyY ? 1 : 0;
  });

  console.log("Top compatible pairs by d_son (eps_son=" + eps + "):");
  for (const c of candidates.slice(0, 5)) {
    console.log(
      `pair ${c.a}/${c.b} mode=${c.mode} age=${c.age_band} d_son=${c.d_son.toFixed(6)} delta_c=${c.delta_c.toFixed(6)}`
    );
  }
}

function main() {
  ensureDir(inbox);
  ensureDir(outPools);

  if (fs.existsSync(poolPath)) {
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const backup = path.join(outPools, `residue_pool.${ts}.json`);
    fs.renameSync(poolPath, backup);
    console.log("Pool archived:", backup);
  }

  const f1 = path.join(inbox, "merge_smoke_a.txt");
  const f2 = path.join(inbox, "merge_smoke_b.txt");
  const f3 = path.join(inbox, "merge_smoke_c.txt");

  writeFile(
    f1,
    [
      "alpha beta gamma",
      "delta epsilon zeta",
      "shared motif line",
      "lambda mu nu",
      "omega line"
    ].join("\n") + "\n"
  );
  writeFile(
    f2,
    [
      "alpha beta gamma",
      "delta epsilon zeta",
      "shared motif line",
      "lambda mu nu",
      "omega line!"
    ].join("\n") + "\n"
  );
  writeFile(
    f3,
    [
      "alpha beta gamma",
      "delta epsilon zeta",
      "shared motif line",
      "extra variant line",
      "omega line"
    ].join("\n") + "\n"
  );

  const eps = "0.5";

  console.log("Ingest A...");
  runNode(["dist/cli.js", "ingest", "--file", f1, "--uri", "codex://merge/1", "--cycle", "0", "--eps", eps]);
  console.log("Ingest B...");
  runNode(["dist/cli.js", "ingest", "--file", f2, "--uri", "codex://merge/2", "--cycle", "0", "--eps", eps]);
  console.log("Ingest C...");
  runNode(["dist/cli.js", "ingest", "--file", f3, "--uri", "codex://merge/3", "--cycle", "0", "--eps", eps]);

  console.log("Round...");
  const roundOut = runNode(["dist/cli.js", "round", "--cycle", "1", "--eps", eps, "--scope", "event"]);
  const roundJson = parseLastJson(roundOut);
  console.log("Round output:", JSON.stringify(roundJson, null, 2));

  const merges = Number(roundJson.merges ?? 0);
  if (merges >= 1) {
    console.log("OK: merges >= 1");
    process.exit(0);
  }

  console.log("FAIL: merges < 1");
  if (fs.existsSync(poolPath)) {
    const pool = JSON.parse(fs.readFileSync(poolPath, "utf8"));
    printCandidates(pool.clusters || [], Number(eps));
  } else {
    console.log("Pool missing:", poolPath);
  }
  process.exit(1);
}

main();


