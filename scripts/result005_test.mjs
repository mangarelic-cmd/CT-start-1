import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = path.resolve(process.cwd());
const outDir = path.resolve(root, "txt");
const outFile = path.resolve(outDir, "result005.txt");

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

function runCmd(cmd, args = []) {
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

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function sumR(v) {
  return v.PI + v.SQRT2 + v.SQRT3 + v.PHI + v.LN5;
}

function fail(msg) {
  writeLine(`RESULT005: FAIL (${msg})`);
  process.exit(1);
}

ensureDir(outDir);
fs.writeFileSync(outFile, "", "utf8");

header("BLOCK A - prepare inputs");
const inboxRoot = path.resolve(root, "data", "inbox", "limits-geometry");
ensureDir(inboxRoot);

const words = [
  "angle",
  "triangle",
  "quadrilatere",
  "carre",
  "rectangle",
  "losange",
  "parallelogramme",
  "polygone",
  "cercle",
  "ellipse",
  "cube",
  "pave",
  "pyramide",
  "tetraedre",
  "prisme",
  "cylindre",
  "cone",
  "sphere",
  "icosaedre",
  "dodecaedre",
  "diagonale",
  "arete",
  "face",
  "sommet",
  "volume",
  "surface",
  "hauteur",
  "base",
  "axe",
  "centre",
  "rotation",
  "translation",
  "symetrie",
  "reflexion",
  "homothetie",
  "projection"
];

const files = [];
for (let i = 0; i < words.length; i++) {
  const n = String(i + 1).padStart(2, "0");
  const name = `${n}_${words[i]}.txt`;
  const abs = path.join(inboxRoot, name);
  fs.writeFileSync(abs, words[i] + "\n", "utf8");
  files.push({ name, abs });
}
writeLine(`entries=${files.length}`);

header("BLOCK B - archive pool");
const poolPath = path.resolve(root, "data", "out", "pools", "residue_pool.json");
if (fs.existsSync(poolPath)) {
  const ts = new Date().toISOString().replace(/[:.]/g, "-");
  const bak = path.resolve(root, "data", "out", "pools", `residue_pool.${ts}.json`);
  fs.renameSync(poolPath, bak);
  writeLine(`pool archived: ${bak}`);
} else {
  writeLine("pool missing: nothing to archive");
}

header("BLOCK C - ingest 36 items (cycle=0, eps=0.0001)");
const outcomes = [];
const seenPackets = new Set();
let countDup = 0;
let countSutured = 0;
let countResidue = 0;

for (const f of files) {
  const uri = `local://limits-geometry/${f.name}`;
  const res = runCmd("node", ["dist/cli.js", "ingest", "--file", f.abs, "--uri", uri, "--cycle", "0", "--eps", "0.0001"]);
  if (res.status !== 0) fail(`ingest ${f.name} failed`);
  const j = parseLastJson(res.stdout || "");
  if (!j || !j.packet_id || !j.status) fail(`ingest ${f.name} missing JSON output`);
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
  outcomes.push({ file: f.name, status: j.status, outcome });
}

writeLine("file\tstatus\toutcome");
for (const row of outcomes) {
  writeLine(`${row.file}\t${row.status}\t${row.outcome}`);
}
writeLine(`count_DUPLICATE=${countDup}`);
writeLine(`count_SUTURED=${countSutured}`);
writeLine(`count_RESIDUE=${countResidue}`);

header("BLOCK D - round 1 (limits-geometry)");
let res = runCmd("npm", ["run", "round", "--", "--cycle", "1", "--eps", "0.0001", "--scope", "limits-geometry"]);
if (res.status !== 0) fail("round 1 failed");
const logsDir = path.resolve(root, "data", "out", "logs");
let roundJson = parseLastJson(res.stdout || "");
if (!roundJson) {
  const roundLog = latestRoundLog(logsDir);
  if (roundLog) roundJson = readJson(path.resolve(logsDir, roundLog));
}
if (!roundJson) fail("round 1 JSON missing");

const merges = Number(roundJson.merges ?? 0);
writeLine(`merges=${merges}`);
writeLine(`clusters_after=${roundJson.clusters_after}`);

const trace = (roundJson.trace_sample || []).filter((t) => t.step === "merge");
if (merges > trace.length) {
  writeLine(`trace_sample_incomplete=merges:${merges} trace:${trace.length}`);
}

const phasesSeen = new Set();
let compressionOk = true;
for (const t of trace) {
  if (t.phase !== undefined) phasesSeen.add(t.phase);
  const maxBefore = Math.max(t.r_before_a, t.r_before_b);
  const ok = t.r_after < maxBefore;
  if (!ok) compressionOk = false;
  writeLine(
    `merge a=${t.a} b=${t.b} phase=${t.phase} sim=${t.sim} w=${t.w} r_after=${t.r_after} max_before=${maxBefore} compression=${ok ? "OK" : "FAIL"}`
  );
}

const poolPostRound = fs.existsSync(poolPath) ? readJson(poolPath) : null;
let multiWord = false;
if (poolPostRound && Array.isArray(poolPostRound.clusters)) {
  for (const c of poolPostRound.clusters) {
    const members = c.member_residue_ids || c.members || c.member_ids || [];
    if (Array.isArray(members) && members.length > 1) {
      multiWord = true;
      break;
    }
  }
}

header("BLOCK E - checks");
writeLine(`DUPLICATE=${countDup}`);
writeLine(`SUTURED=${countSutured}`);
writeLine(`RESIDUE=${countResidue}`);
writeLine(`merges>0=${merges > 0 ? "OUI" : "NON"}`);
writeLine(`merges_total=${merges}`);
writeLine(`cluster_multi_mots=${multiWord ? "OUI" : "NON"}`);
writeLine(`phases_observees=${[...phasesSeen].sort().join(",") || "none"}`);
writeLine(`compression_all_merges=${compressionOk ? "OK" : "FAIL"}`);

header("BLOCK F - round 2 idempotence");
res = runCmd("npm", ["run", "round", "--", "--cycle", "1", "--eps", "0.0001", "--scope", "limits-geometry"]);
if (res.status !== 0) fail("round 2 failed");
let roundJson2 = parseLastJson(res.stdout || "");
if (!roundJson2) {
  const roundLog = latestRoundLog(logsDir);
  if (roundLog) roundJson2 = readJson(path.resolve(logsDir, roundLog));
}
if (!roundJson2) fail("round 2 JSON missing");
writeLine(`round1.merges=${merges} round2.merges=${roundJson2.merges}`);

const idempotent = Number(roundJson2.merges ?? 0) === 0;

let verdict = "PASS";
let reason = "All required checks met";
if (!idempotent) {
  verdict = "FAIL";
  reason = "Second round produced merges";
} else if (!compressionOk) {
  verdict = "FAIL";
  reason = "Compression check failed for at least one merge";
} else if (merges > trace.length) {
  verdict = "FAIL";
  reason = "Trace sample shorter than merge count";
}

writeLine("");
writeLine(`RESULT005: ${verdict} (${reason}).`);
process.exit(verdict === "PASS" ? 0 : 1);
