import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = path.resolve(process.cwd());
const outDir = path.resolve(root, "txt");
const outFile = path.resolve(outDir, "result004.txt");

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
  writeLine(`RESULT004: FAIL (${msg})`);
  process.exit(1);
}

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function preview(text, maxLen = 60) {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen - 3) + "...";
}

ensureDir(outDir);
fs.writeFileSync(outFile, "", "utf8");

header("BLOCK A - build check");
const distCli = path.resolve(root, "dist", "cli.js");
if (!fs.existsSync(distCli)) {
  const res = runCmd("build:all", "npm", ["run", "build:all"]);
  if (res.status !== 0) fail("build:all failed");
} else {
  writeLine("dist/cli.js exists; skip build");
}

header("BLOCK B - prepare inputs");
const inboxRoot = path.resolve(root, "data", "inbox", "generated", "results004");
ensureDir(inboxRoot);

function writeFile(name, content) {
  fs.writeFileSync(path.join(inboxRoot, name), content, "utf8");
}

const phrases = [
  { id: "01", text: "The river is calm at noon." },
  { id: "02", text: "The river is calm at noon!" },
  { id: "03", text: "the river is calm at noon." },
  { id: "04", text: "The river is calm at noon today." },
  { id: "05", text: "The river is quiet at noon." },
  { id: "06", text: "Pack items: map, water, rope, torch." },
  { id: "07", text: "Pack items: rope, torch, map, water." },
  { id: "08", text: "Pack items: water, map, torch, rope." },
  { id: "09", text: "Pack items: torch, rope, water, map." },
  { id: "10", text: "Pack items: map, rope, water, torch." },
  { id: "11", text: "In reviews, keep the core steady and note the edges." },
  { id: "12", text: "For pilots, keep the core steady while the wings adjust." },
  { id: "13", text: "At noon, keep the core steady even if the crowd shifts." },
  { id: "14", text: "When coding, keep the core steady; refactor the shell." },
  { id: "15", text: "In a storm, keep the core steady and trim the sail." },
  { id: "16", text: "A brass key opened the old blue door." },
  { id: "17", text: "She counted seven steps then stopped." },
  { id: "18", text: "Winter light fell on a silent market." },
  { id: "19", text: "We met at the bridge and traded notes." },
  { id: "20", text: "The cat slept under the warm printer." }
];

const equations = [
  { id: "01", text: "y = a + b" },
  { id: "02", text: "y=a+b" },
  { id: "03", text: "y = b + a" },
  { id: "04", text: "y = a + b + 0" },
  { id: "05", text: "y = a + b" },
  { id: "06", text: "a(b + c) = ab + ac" },
  { id: "07", text: "ab + ac = a(b+c)" },
  { id: "08", text: "sin(x)^2 + cos(x)^2 = 1" },
  { id: "09", text: "1 = cos(x)^2 + sin(x)^2" },
  { id: "10", text: "(x+1)^2 = x^2 + 2x + 1" },
  { id: "11", text: "k*(m+n) + r = k*m + k*n + r" },
  { id: "12", text: "k*(m+n) - r = k*m + k*n - r" },
  { id: "13", text: "2*k*(m+n) = 2*k*m + 2*k*n" },
  { id: "14", text: "k*(m+n) = k*m + k*n" },
  { id: "15", text: "q + k*(m+n) + s" },
  { id: "16", text: "F = m*a" },
  { id: "17", text: "E = m*c^2" },
  { id: "18", text: "p = (v1 + v2)/2" },
  { id: "19", text: "det(A) = a*d - b*c" },
  { id: "20", text: "x^3 - 3x + 1 = 0" }
];

for (const p of phrases) {
  writeFile(`phrase_${p.id}.txt`, p.text + "\n");
}
for (const e of equations) {
  writeFile(`equation_${e.id}.txt`, e.text + "\n");
}

header("DATASET - phrases");
for (const p of phrases) {
  writeLine(`${p.id}. ${preview(p.text)}`);
}
header("DATASET - equations");
for (const e of equations) {
  writeLine(`${e.id}. ${preview(e.text)}`);
}

header("BLOCK B2 - archive pool");
const poolPath = path.resolve(root, "data", "out", "pools", "residue_pool.json");
if (fs.existsSync(poolPath)) {
  const bak = path.resolve(
    root,
    "data",
    "out",
    "pools",
    `residue_pool.${Date.now()}.json`
  );
  fs.renameSync(poolPath, bak);
  writeLine(`pool archived: ${bak}`);
}

header("BLOCK C - ingest 40 items");
const outcomes = [];
const seenPackets = new Set();
let countDup = 0;
let countSutured = 0;
let countResidue = 0;

for (const p of phrases) {
  const abs = path.resolve(inboxRoot, `phrase_${p.id}.txt`);
  const uri = `local://results004/phrase/${p.id}`;
  const res = runCmd("ingest", "node", [
    "dist/cli.js",
    "ingest",
    "--file",
    abs,
    "--uri",
    uri,
    "--cycle",
    "0",
    "--eps",
    "0.5"
  ]);
  if (res.status !== 0) fail(`ingest phrase_${p.id} failed`);
  const j = parseLastJson(res.stdout || "");
  if (!j || !j.packet_id || !j.status) fail(`ingest phrase_${p.id} missing JSON`);
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
  outcomes.push({ file: `phrase_${p.id}.txt`, status: j.status, outcome });
}

for (const e of equations) {
  const abs = path.resolve(inboxRoot, `equation_${e.id}.txt`);
  const uri = e.id === "05"
    ? "local://results004/equation/01"
    : `local://results004/equation/${e.id}`;
  const res = runCmd("ingest", "node", [
    "dist/cli.js",
    "ingest",
    "--file",
    abs,
    "--uri",
    uri,
    "--cycle",
    "0",
    "--eps",
    "0.5"
  ]);
  if (res.status !== 0) fail(`ingest equation_${e.id} failed`);
  const j = parseLastJson(res.stdout || "");
  if (!j || !j.packet_id || !j.status) fail(`ingest equation_${e.id} missing JSON`);
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
  outcomes.push({ file: `equation_${e.id}.txt`, status: j.status, outcome });
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
const clustersBefore = poolPostIngest && Array.isArray(poolPostIngest.clusters)
  ? poolPostIngest.clusters.length
  : null;
if (clustersBefore !== null) writeLine(`clusters_before=${clustersBefore}`);

header("BLOCK D - round 1");
let res = runCmd("round-1", "node", [
  "dist/cli.js",
  "round",
  "--cycle",
  "1",
  "--eps",
  "0.5",
  "--scope",
  "event"
]);
if (res.status !== 0) fail("round 1 failed");
const logsDir = path.resolve(root, "data", "out", "logs");
let roundJson = parseLastJson(res.stdout || "");
let roundLog = null;
if (!roundJson) {
  roundLog = latestRoundLog(logsDir);
  if (roundLog) roundJson = readJson(path.resolve(logsDir, roundLog));
}
if (!roundJson) fail("round 1 JSON missing");
const clustersAfter = roundJson.clusters_after ?? null;
if (roundJson.merges === undefined) fail("round 1 merges missing");
writeLine(`merges_round1=${roundJson.merges}`);
if (clustersAfter !== null) writeLine(`clusters_after=${clustersAfter}`);

const stamp = Date.now();
if (roundLog) {
  const src = path.resolve(logsDir, roundLog);
  const dst = path.resolve(logsDir, `tmp_results004_${stamp}_round1.log.json`);
  fs.copyFileSync(src, dst);
  writeLine(`round1 log copied: ${dst}`);
}

if (roundJson.merges <= 0) fail("merges=0 in round 1");
const trace = (roundJson.trace_sample || []).filter((t) => t.step === "merge");
if (trace.length === 0) fail("trace_sample missing merges");
const sample = trace.slice(0, 10);
writeLine("merge_sample (up to 10):");
let foundCycle = false;
for (const t of sample) {
  if (
    t.d_son === undefined ||
    t.sim === undefined ||
    t.phase === undefined ||
    t.w === undefined ||
    t.r_before_a === undefined ||
    t.r_before_b === undefined ||
    t.r_after === undefined
  ) {
    fail("merge trace missing fields");
  }
  const maxBefore = Math.max(t.r_before_a, t.r_before_b);
  if (!(t.r_after < maxBefore)) fail("compression/gain violated");
  if (t.phase === "cycle" && t.sim >= 0.946 && Number(t.w) === 0) {
    foundCycle = true;
  }
  writeLine(
    `d_son=${t.d_son} sim=${t.sim} phase=${t.phase} w=${t.w} ` +
    `r_before_a=${t.r_before_a} r_before_b=${t.r_before_b} r_after=${t.r_after}`
  );
}
if (!foundCycle) fail("no cycle merge with sim>=0.946 and w=0");

header("BLOCK E - round 2 idempotence");
res = runCmd("round-2", "node", [
  "dist/cli.js",
  "round",
  "--cycle",
  "1",
  "--eps",
  "0.5",
  "--scope",
  "event"
]);
if (res.status !== 0) fail("round 2 failed");
let roundJson2 = parseLastJson(res.stdout || "");
let roundLog2 = null;
if (!roundJson2) {
  roundLog2 = latestRoundLog(logsDir);
  if (roundLog2) roundJson2 = readJson(path.resolve(logsDir, roundLog2));
}
if (!roundJson2) fail("round 2 JSON missing");
if (roundLog2) {
  const src = path.resolve(logsDir, roundLog2);
  const dst = path.resolve(logsDir, `tmp_results004_${stamp}_round2.log.json`);
  fs.copyFileSync(src, dst);
  writeLine(`round2 log copied: ${dst}`);
}
if (roundJson2.merges !== 0) fail("round 2 merges != 0");
writeLine(`merges_round2=${roundJson2.merges}`);
if (
  roundJson2.clusters_after !== undefined &&
  roundJson.clusters_after !== undefined &&
  roundJson2.clusters_after !== roundJson.clusters_after
) {
  fail("clusters_after changed on round 2");
}

header("BLOCK F - recap");
writeLine(`counts: DUPLICATE=${countDup} SUTURED=${countSutured} RESIDUE=${countResidue}`);
writeLine(`merges_round1=${roundJson.merges} merges_round2=${roundJson2.merges}`);
if (clustersBefore !== null && clustersAfter !== null) {
  writeLine(`clusters_before=${clustersBefore} clusters_after=${clustersAfter}`);
}

if (countDup < 1 || countSutured < 1 || countResidue < 1) {
  fail("missing one of DUPLICATE/SUTURED/RESIDUE outcomes");
}

writeLine("RESULT004: PASS");
process.exit(0);
