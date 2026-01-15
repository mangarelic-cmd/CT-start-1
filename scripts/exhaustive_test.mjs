import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = path.resolve(process.cwd());
const outDir = path.resolve(root, "txt");
const outFile = path.resolve(outDir, "result001.txt");

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

function fail(testName, msg) {
  writeLine(`FAIL ${testName}: ${msg}`);
  process.exit(1);
}

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function findLatestContractLog(logsDir) {
  if (!fs.existsSync(logsDir)) return null;
  const files = fs.readdirSync(logsDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => ({ f, t: fs.statSync(path.join(logsDir, f)).mtimeMs }));

  const contract = files.filter((x) => x.f.toLowerCase().includes("contract"));
  const tmp = files.filter((x) => x.f.toLowerCase().includes("tmp"));

  const pick = (arr) => arr.sort((a, b) => b.t - a.t)[0];
  return (pick(contract) || pick(tmp))?.f || null;
}

function validatePhi5(jsonPath, testName) {
  const j = readJson(jsonPath);
  const phi = j?.final?.phi || {};
  const keys = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"];
  const foundKeys = Object.keys(phi);
  if (foundKeys.length !== keys.length || !keys.every((k) => k in phi)) {
    fail(testName, `phi keys invalid: ${JSON.stringify(foundKeys)}`);
  }
  for (const k of keys) {
    const v = Number(phi[k]);
    if (!Number.isFinite(v)) fail(testName, `non-finite ${k}`);
  }
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

writeLine(`UTC: ${new Date().toISOString()}`);
writeLine(`cwd: ${root}`);

// Versions
header("HEADER");
writeLine(`node: ${process.version}`);
const npmRes = runCmd("npm-version", "npm", ["-v"]);
if (npmRes.status !== 0) fail("HEADER", "npm -v failed");

// Git info
const gitSha = spawnSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" });
if (gitSha.status === 0) {
  writeLine(`git sha: ${gitSha.stdout.trim()}`);
} else {
  writeLine("git sha: unavailable");
}
const gitStatus = spawnSync("git", ["status", "--porcelain"], { encoding: "utf8" });
if (gitStatus.status === 0) {
  writeLine("git status --porcelain:");
  writeLine(gitStatus.stdout.trim() || "(clean)");
} else {
  writeLine("git status --porcelain: unavailable");
}

// TEST A
header("TEST A");
let res = runCmd("build:all", "npm", ["run", "build:all"]);
if (res.status !== 0) fail("TEST A", "build:all failed");
res = runCmd("test:cvm-contract", "npm", ["run", "test:cvm-contract"]);
if (res.status !== 0) fail("TEST A", "test:cvm-contract failed");
const logsDir = path.resolve(root, "data", "out", "logs");
let contractPath = path.join(logsDir, "tmp_cvm_contract.json");
if (!fs.existsSync(contractPath)) {
  const latest = findLatestContractLog(logsDir);
  if (!latest) fail("TEST A", "no contract log found");
  contractPath = path.join(logsDir, latest);
}
validatePhi5(contractPath, "TEST A");
writeLine("PASS TEST A");

// TEST B
header("TEST B");
const outPath = path.resolve(root, "data", "out");
let backupOut = null;
if (fs.existsSync(outPath)) {
  backupOut = `${outPath}.__bak_${Date.now()}`;
  fs.renameSync(outPath, backupOut);
  writeLine(`backup: ${backupOut}`);
}
const needDirs = ["logs", "packets", "residue", "pools", "skins"];
for (const d of needDirs) ensureDir(path.join(outPath, d));
writeLine("created data/out structure");

// TEST C (E2E run)
header("TEST C");
const inbox = path.resolve(root, "data", "inbox", "__e2e_exhaustive__");
ensureDir(inbox);
const aPath = path.join(inbox, "a.txt");
const bPath = path.join(inbox, "b.txt");
const cPath = path.join(inbox, "c.txt");
const aLines = [
  "line one alpha",
  "line two beta",
  "line three gamma",
  "line four delta",
  "line five epsilon",
  "line six zeta",
  "line seven eta",
  "line eight theta"
];
const bLines = [...aLines];
bLines[3] = "line four delta!";
const cLines = [
  aLines[0],
  aLines[1],
  aLines[2],
  aLines[3],
  "line nine iota",
  "line ten kappa",
  "line eleven lambda",
  "line twelve mu"
];
fs.writeFileSync(aPath, aLines.join("\n") + "\n", "utf8");
fs.writeFileSync(bPath, bLines.join("\n") + "\n", "utf8");
fs.writeFileSync(cPath, cLines.join("\n") + "\n", "utf8");

const poolPath = path.resolve(outPath, "pools", "residue_pool.json");
if (fs.existsSync(poolPath)) {
  const bak = path.join(outPath, "pools", `residue_pool.__bak_${Date.now()}.json`);
  fs.renameSync(poolPath, bak);
  writeLine(`pool backup: ${bak}`);
}

const ingestCmd = (file, uri) =>
  runCmd("ingest", "node", ["dist/cli.js", "ingest", "--file", file, "--uri", uri, "--cycle", "0", "--eps", "0.5"]);

res = ingestCmd(aPath, "codex://exhaustive/a");
if (res.status !== 0) fail("TEST C", "ingest a failed");
res = ingestCmd(bPath, "codex://exhaustive/b");
if (res.status !== 0) fail("TEST C", "ingest b failed");
res = ingestCmd(cPath, "codex://exhaustive/c");
if (res.status !== 0) fail("TEST C", "ingest c failed");

res = runCmd("round", "node", ["dist/cli.js", "round", "--cycle", "1", "--eps", "0.5", "--scope", "event"]);
if (res.status !== 0) fail("TEST C", "round failed");

let roundJson = parseLastJson(res.stdout || "");
if (!roundJson) {
  const roundLog = latestRoundLog(logsDir);
  if (roundLog) {
    try {
      roundJson = readJson(path.join(logsDir, roundLog));
    } catch {
      roundJson = null;
    }
  }
}

if (!roundJson) fail("TEST C", "round output JSON not found");
writeLine(`round.merges: ${roundJson.merges}`);
writeLine(`round.clusters_after: ${roundJson.clusters_after}`);

const pool = fs.existsSync(poolPath) ? readJson(poolPath) : null;
if (!pool || !Array.isArray(pool.clusters)) fail("TEST C", "pool JSON invalid");

if (roundJson.merges > 0) {
  const trace = (roundJson.trace_sample || []).slice(0, 2);
  writeLine("trace_sample (first 2):");
  writeLine(JSON.stringify(trace, null, 2));
  const hasFields = trace.every((t) => t.phase && t.sim !== undefined && t.w !== undefined);
  if (!hasFields) fail("TEST C", "trace missing required fields");
} else {
  // explain why merges==0
  const clusters = pool.clusters;
  const pairs = [];
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
}

// TEST D
header("TEST D");
res = runCmd("round-2", "node", ["dist/cli.js", "round", "--cycle", "1", "--eps", "0.5", "--scope", "event"]);
if (res.status !== 0) fail("TEST D", "round-2 failed");
let roundJson2 = parseLastJson(res.stdout || "");
if (!roundJson2) {
  const roundLog = latestRoundLog(logsDir);
  if (roundLog) {
    try {
      roundJson2 = readJson(path.join(logsDir, roundLog));
    } catch {
      roundJson2 = null;
    }
  }
}
if (!roundJson2) fail("TEST D", "round-2 output JSON not found");
writeLine(`round-1 merges: ${roundJson.merges}`);
writeLine(`round-2 merges: ${roundJson2.merges}`);
writeLine(`round-1 clusters_after: ${roundJson.clusters_after}`);
writeLine(`round-2 clusters_after: ${roundJson2.clusters_after}`);
if (roundJson2.merges > 0) fail("TEST D", "non-idempotent merges");
if (roundJson2.clusters_after !== roundJson.clusters_after) {
  fail("TEST D", "clusters_after mismatch");
}
writeLine("PASS TEST D");

// TEST E
header("TEST E");
const writeTest = path.join(logsDir, "__write_test.txt");
fs.writeFileSync(writeTest, "ok", "utf8");
fs.unlinkSync(writeTest);
writeLine("PASS TEST E");

// TEST F
header("TEST F");
const distFiles = ["cli.js", "cvm_bridge.js", "residue_pool.js"].map((f) => path.join(root, "dist", f));
const srcFiles = ["cli.ts", "cvm_bridge.ts", "residue_pool.ts"].map((f) => path.join(root, "src", f));
for (let i = 0; i < distFiles.length; i++) {
  const d = distFiles[i];
  const s = srcFiles[i];
  if (!fs.existsSync(d) || !fs.existsSync(s)) fail("TEST F", `missing ${d} or ${s}`);
  const dTime = fs.statSync(d).mtimeMs;
  const sTime = fs.statSync(s).mtimeMs;
  writeLine(`${path.basename(d)} mtime=${dTime} src=${sTime} newer=${dTime > sTime}`);
  if (!(dTime > sTime)) fail("TEST F", "dist not newer than src; run npm run build:all");
}
writeLine("PASS TEST F");

// Restore data/out if backup exists
if (backupOut) {
  if (fs.existsSync(outPath)) fs.rmSync(outPath, { recursive: true, force: true });
  fs.renameSync(backupOut, outPath);
  writeLine(`restored: ${outPath}`);
}

// FINAL SUMMARY
header("FINAL SUMMARY");
writeLine("TEST A: PASS");
writeLine("TEST B: PASS");
writeLine("TEST C: PASS");
writeLine("TEST D: PASS");
writeLine("TEST E: PASS");
writeLine("TEST F: PASS");

process.exit(0);
