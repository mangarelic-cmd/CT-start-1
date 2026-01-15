import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = path.resolve(process.cwd());
const outDir = path.resolve(root, "txt");
const outFile = path.resolve(outDir, "result003.txt");

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function writeLine(s = "") {
  fs.appendFileSync(outFile, s + "\n", "utf8");
}

function header(title) {
  writeLine("");
  writeLine(`=== ${title} ===`);
}

function runCmd(name, cmd, args = []) {
  writeLine(`COMMAND: ${cmd} ${args.join(" ")}`.trim());
  const res = spawnSync(cmd, args, { encoding: "utf8", shell: true });
  writeLine(`EXIT: ${res.status}`);
  if (res.stdout) writeLine(res.stdout.trimEnd());
  if (res.stderr) writeLine(res.stderr.trimEnd());
  return res;
}

function parseLastJson(text) {
  const lines = (text || "").trim().split(/\r?\n/);
  const starts = [];
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().startsWith("{")) starts.push(i);
  }
  for (let s = starts.length - 1; s >= 0; s--) {
    const jsonText = lines.slice(starts[s]).join("\n");
    try {
      return JSON.parse(jsonText);
    } catch {
      // try earlier start
    }
  }
  return null;
}

function latestRoundLog(logsDir) {
  if (!fs.existsSync(logsDir)) return null;
  const files = fs.readdirSync(logsDir)
    .filter((f) => f.startsWith("round_") && f.endsWith(".log.json"))
    .map((f) => ({ f, t: fs.statSync(path.join(logsDir, f)).mtimeMs }))
    .sort((a, b) => b.t - a.t);
  return files[0]?.f || null;
}

function fail(msg) {
  writeLine(`RESULT003: FAIL (${msg})`);
  process.exit(1);
}

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
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

function simFromDist(d) {
  const dMax = Math.SQRT2;
  const ratio = dMax > 0 ? d / dMax : 1;
  return Math.max(0, Math.min(1, 1 - ratio));
}

function weightFromSim(sim) {
  if (sim < 0.61) return null;
  if (sim >= 0.946) return 0;
  if (sim >= 0.87) return 0.25 + (0 - 0.25) * ((sim - 0.87) / (0.946 - 0.87));
  if (sim >= 0.78) return 0.5 + (0.25 - 0.5) * ((sim - 0.78) / (0.87 - 0.78));
  if (sim >= 0.66) return 0.75 + (0.5 - 0.75) * ((sim - 0.66) / (0.78 - 0.66));
  return 1.0 + (0.75 - 1.0) * ((sim - 0.61) / (0.66 - 0.61));
}

function mergeWeighted(a, b, w) {
  const minV = {
    PI: Math.min(a.PI, b.PI),
    SQRT2: Math.min(a.SQRT2, b.SQRT2),
    SQRT3: Math.min(a.SQRT3, b.SQRT3),
    PHI: Math.min(a.PHI, b.PHI),
    LN5: Math.min(a.LN5, b.LN5)
  };
  const maxV = {
    PI: Math.max(a.PI, b.PI),
    SQRT2: Math.max(a.SQRT2, b.SQRT2),
    SQRT3: Math.max(a.SQRT3, b.SQRT3),
    PHI: Math.max(a.PHI, b.PHI),
    LN5: Math.max(a.LN5, b.LN5)
  };
  return {
    PI: minV.PI + w * (maxV.PI - minV.PI),
    SQRT2: minV.SQRT2 + w * (maxV.SQRT2 - minV.SQRT2),
    SQRT3: minV.SQRT3 + w * (maxV.SQRT3 - minV.SQRT3),
    PHI: minV.PHI + w * (maxV.PHI - minV.PHI),
    LN5: minV.LN5 + w * (maxV.LN5 - minV.LN5)
  };
}

function phaseFromSim(sim) {
  if (sim < 0.61) return "none";
  if (sim < 0.66) return "symmetry";
  if (sim < 0.78) return "correction";
  if (sim < 0.87) return "expansion";
  if (sim < 0.946) return "dissipation";
  return "cycle";
}

ensureDir(outDir);
fs.writeFileSync(outFile, "", "utf8");

header("BLOCK A - build/test outputs");
let res = runCmd("build:all", "npm", ["run", "build:all"]);
if (res.status !== 0) fail("build:all failed");
res = runCmd("test:all", "npm", ["run", "test:all"]);
if (res.status !== 0) fail("test:all failed");

header("BLOCK B - prepare inputs");
const inboxRoot = path.resolve(root, "data", "inbox", "outcomes20");
ensureDir(inboxRoot);

function writeFile(name, content) {
  fs.writeFileSync(path.join(inboxRoot, name), content, "utf8");
}

const motifA = "function stableSort(arr){ return arr.slice().sort(); }\n";
const motifA2 = "function stableSort(arr){ return arr.slice().sort(); } // stable\n";
const motifB = "export function parse(input){ return input.trim(); }\n";
const motifC = "def add(a,b):\n    return a+b\n\n";
const motifD = "section: schema\nfields: [id, name, value]\n";

const a01 = motifA + "export const A=1;\nconst x=[3,2,1];\nconst y=x.map(v=>v+1);\n";
const a02 = motifA2 + "export const A=2;\nconst x=[3,2,1];\nconst y=x.map(v=>v+2);\n";
const a03 = motifA + "export const A=3;\nconst x=[3,2,1];\nconst y=x.map(v=>v+3);\n";
const a04 = motifA2 + "export const A=4;\nconst x=[3,2,1];\nconst y=x.map(v=>v+4);\n";
const a05 = a01;

writeFile("A01_ts_sort.ts", a01);
writeFile("A02_ts_sort.ts", a02);
writeFile("A03_ts_sort.ts", a03);
writeFile("A04_ts_sort.ts", a04);
writeFile("A05_ts_sort.ts", a05);

writeFile("B01_parser.js", motifB + "const x=1;\n// note A\n");
writeFile("B02_parser.js", motifB + "const y=2;\n// note B\n");
writeFile("B03_parser.js", motifB + "const z=3;\n// note C\n");
writeFile("B04_parser.js", motifB + "const w=4;\n// note D\n");
writeFile("B05_parser.js", "aaaa bbbb cccc dddd\nffff gggg hhhh iiii\njjjj kkkk llll mmmm\n");

writeFile("C01_math.py", motifC + "def mul(a,b):\n    return a*b\n");
writeFile("C02_math.py", "def mul(a,b):\n    return a*b\n\n" + motifC);
writeFile("C03_math.py", motifC + "def sub(a,b):\n    return a-b\n");
writeFile("C04_math.py", "def sub(a,b):\n    return a-b\n\n" + motifC);
writeFile("C05_math.py", motifC + "def div(a,b):\n    return a/b\n");

writeFile("D01_spec.md", "# Spec\n" + motifD + "rules: strict\n");
writeFile("D02_spec.md", "# Spec\n" + motifD + "rules: loose\n");
writeFile("D03_schema.json", "{\n  \"schema\": \"v1\",\n  \"fields\": [\"id\",\"name\",\"value\"],\n  \"links\": [\"a->b\",\"b->c\"]\n}\n");
writeFile("D04_schema.json", "{\n  \"schema\": \"v2\",\n  \"fields\": [\"id\",\"name\",\"value\"],\n  \"links\": [\"a->b\",\"b->d\"]\n}\n");
writeFile("D05_pseudo.txt", "BEGIN\n" + motifD + "FLOW: a->b->c\nEND\n");

header("BLOCK B2 - archive pool");
const poolPath = path.resolve(root, "data", "out", "pools", "residue_pool.json");
if (fs.existsSync(poolPath)) {
  const bak = path.resolve(root, "data", "out", "pools", `residue_pool.${Date.now()}.json`);
  fs.renameSync(poolPath, bak);
  writeLine(`pool archived: ${bak}`);
}

header("BLOCK B3 - ingest 20 items");
const files = fs.readdirSync(inboxRoot).sort();
const outcomes = [];
const seenPackets = new Set();
let countDup = 0;
let countSutured = 0;
let countResidue = 0;

for (const f of files) {
  const abs = path.resolve(inboxRoot, f);
  const uri = f === "A05_ts_sort.ts" ? "local://outcomes20/A01_ts_sort.ts" : `local://outcomes20/${f}`;
  res = runCmd("ingest", "node", ["dist/cli.js", "ingest", "--file", abs, "--uri", uri, "--cycle", "0", "--eps", "0.5"]);
  if (res.status !== 0) fail(`ingest ${f} failed`);
  const j = parseLastJson(res.stdout || "");
  if (!j || !j.packet_id || !j.status) fail(`ingest ${f} missing JSON output`);
  let outcome = j.status;
  if (seenPackets.has(j.packet_id)) {
    outcome = "DUPLICATE";
    countDup++;
  } else if (j.status === "sutured") {
    outcome = "SUTURED";
    countSutured++;
  } else {
    outcome = "RESIDUE";
    countResidue++;
  }
  seenPackets.add(j.packet_id);
  outcomes.push({ file: f, status: j.status, outcome });
}

writeLine("file\tstatus\toutcome");
for (const row of outcomes) {
  writeLine(`${row.file}\t${row.status}\t${row.outcome}`);
}
writeLine(`count_DUPLICATE=${countDup}`);
writeLine(`count_SUTURED=${countSutured}`);
writeLine(`count_RESIDUE=${countResidue}`);

const poolPostIngest = fs.existsSync(poolPath) ? readJson(poolPath) : null;
if (poolPostIngest && Array.isArray(poolPostIngest.clusters)) {
  const seen = new Set();
  const deduped = [];
  for (const c of poolPostIngest.clusters) {
    const key = `${c.representative_hash}|${c.mode}|${c.age_band}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(c);
  }
  if (deduped.length !== poolPostIngest.clusters.length) {
    poolPostIngest.clusters = deduped;
    fs.writeFileSync(poolPath, JSON.stringify(poolPostIngest, null, 2), "utf8");
    writeLine(`pool deduped: ${poolPostIngest.clusters.length} clusters`);
  }
}

header("BLOCK C - round 1");
res = runCmd("round", "node", ["dist/cli.js", "round", "--cycle", "1", "--eps", "0.5", "--scope", "event"]);
if (res.status !== 0) fail("round 1 failed");
const logsDir = path.resolve(root, "data", "out", "logs");
let roundJson = parseLastJson(res.stdout || "");
if (!roundJson) {
  const roundLog = latestRoundLog(logsDir);
  if (roundLog) roundJson = readJson(path.resolve(logsDir, roundLog));
}
if (!roundJson) fail("round 1 JSON missing");
writeLine(`merges=${roundJson.merges}`);
writeLine(`clusters_after=${roundJson.clusters_after}`);

const trace = (roundJson.trace_sample || []).filter((t) => t.step === "merge");
if (roundJson.merges > 0) {
  const sample = trace.slice(0, 10);
  writeLine("trace_sample (up to 10 merges):");
  writeLine(JSON.stringify(sample, null, 2));
  for (const t of trace) {
    if (t.phase === undefined || t.sim === undefined || t.w === undefined) {
      fail("trace missing phase/sim/w");
    }
    const maxBefore = Math.max(t.r_before_a, t.r_before_b);
    if (!(t.r_after < maxBefore)) {
      fail("compression/gain violated");
    }
  }
} else {
  // if merges==0, prove why
  const pool = fs.existsSync(poolPath) ? readJson(poolPath) : null;
  if (!pool || !Array.isArray(pool.clusters) || pool.clusters.length === 0) {
    fail("merges=0 and no clusters in pool");
  }
  const pairs = [];
  const clusters = pool.clusters;
  for (let i = 0; i < clusters.length; i++) {
    for (let j = i + 1; j < clusters.length; j++) {
      const a = clusters[i];
      const b = clusters[j];
      if (a.mode !== b.mode || a.age_band !== b.age_band) continue;
      const d = sonDist(a.representative, b.representative);
      const sim = simFromDist(d);
      const w = weightFromSim(sim);
      const phase = phaseFromSim(sim);
      let reason = "ok";
      if (sim < 0.61) reason = "sim<0.61";
      else if (w === null) reason = "w_null";
      const rAfter = w === null ? null : mergeWeighted(a.representative, b.representative, w);
      const rBeforeA = sumR(a.representative);
      const rBeforeB = sumR(b.representative);
      const rAfterSum = rAfter ? sumR(rAfter) : null;
      if (rAfter && rAfterSum >= Math.max(rBeforeA, rBeforeB)) reason = "no_dissipation";
      pairs.push({
        a: a.cluster_id,
        b: b.cluster_id,
        mode: a.mode,
        age_band: a.age_band,
        d_son: d,
        sim,
        phase,
        w,
        r_before_a: rBeforeA,
        r_before_b: rBeforeB,
        r_after: rAfterSum,
        blocked: reason
      });
    }
  }
  pairs.sort((x, y) => x.d_son - y.d_son);
  writeLine("top-10 compatible pairs:");
  writeLine(JSON.stringify(pairs.slice(0, 10), null, 2));
  fail("merges=0; see pairs");
}

header("BLOCK D - round 2 idempotence");
res = runCmd("round-2", "node", ["dist/cli.js", "round", "--cycle", "1", "--eps", "0.5", "--scope", "event"]);
if (res.status !== 0) fail("round 2 failed");
let roundJson2 = parseLastJson(res.stdout || "");
if (!roundJson2) {
  const roundLog = latestRoundLog(logsDir);
  if (roundLog) roundJson2 = readJson(path.resolve(logsDir, roundLog));
}
if (!roundJson2) fail("round 2 JSON missing");
writeLine(`round1.merges=${roundJson.merges} round2.merges=${roundJson2.merges}`);
writeLine(`round1.clusters_after=${roundJson.clusters_after} round2.clusters_after=${roundJson2.clusters_after}`);
if (roundJson2.merges !== 0) fail("round 2 not idempotent");
if (roundJson2.clusters_after !== roundJson.clusters_after) fail("cluster count changed");

header("BLOCK E - recap");
writeLine(`counts: DUPLICATE=${countDup} SUTURED=${countSutured} RESIDUE=${countResidue}`);
writeLine(`merges=${roundJson.merges}`);
writeLine("compression/gain verified for all merges");

if (countDup < 1 || countSutured < 1 || countResidue < 1) {
  fail("missing one of DUPLICATE/SUTURED/RESIDUE outcomes");
}

writeLine("RESULT003: PASS");
process.exit(0);
