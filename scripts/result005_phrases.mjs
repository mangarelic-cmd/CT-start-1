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

function runCmd(cmd, args = []) {
  const res = spawnSync(cmd, args, { encoding: "utf8", shell: true });
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

function fail(msg) {
  writeLine(`RESULT005: FAIL (${msg})`);
  process.exit(1);
}

ensureDir(outDir);
fs.writeFileSync(outFile, "", "utf8");

// A) Dataset
const inboxRoot = path.resolve(root, "data", "inbox", "tmp_result005");
ensureDir(inboxRoot);

const phrases = [
  "FORME: carre | DECOMP: 2 triangles | NOTE: rotation 90",
  "FORME: carré | DECOMP: 2 triangles | NOTE: rotation 90°",
  "FORME: carre | DECOMP: deux triangles | NOTE: rotation 90",
  "FORME: carre | DECOMP: 2 triangles | NOTE: rotation=90",
  "FORME: carre | DECOMP: 2 triangles | NOTE: rotation 180",
  "FORME: cube | DECOMP: 2 pyramides | NOTE: axe centre",
  "FORME: cube | DECOMP: deux pyramides | NOTE: axe centre",
  "FORME: cube | DECOMP: 2 pyramides | NOTE: axe-centre",
  "FORME: cube | DECOMP: 2 pyramides | NOTE: axe=centre",
  "FORME: cube | DECOMP: 2 pyramides | NOTE: axe coin",
  "FORME: rectangle | DECOMP: 2 triangles | NOTE: diagonale",
  "FORME: rectangle | DECOMP: deux triangles | NOTE: diagonale",
  "FORME: rectangle | DECOMP: 2 triangles | NOTE: diagonale 1",
  "FORME: rectangle | DECOMP: 2 triangles | NOTE: diagonale=1",
  "FORME: rectangle | DECOMP: 2 triangles | NOTE: diagonale 2",
  "FORME: pyramide | DECOMP: 4 triangles | NOTE: faces",
  "FORME: pyramide | DECOMP: quatre triangles | NOTE: faces",
  "FORME: pyramide | DECOMP: 4 triangles | NOTE: faces+base",
  "FORME: pyramide | DECOMP: 4 triangles | NOTE: faces base",
  "FORME: pyramide | DECOMP: 4 triangles | NOTE: faces (base)"
];

const files = [];
for (let i = 0; i < phrases.length; i++) {
  const n = String(i + 1).padStart(2, "0");
  const name = `${n}.txt`;
  const abs = path.join(inboxRoot, name);
  fs.writeFileSync(abs, phrases[i] + "\n", "utf8");
  files.push({ name, abs });
}

writeLine("A) Dataset");
writeLine("nb_inputs = 20");
writeLine("groups_expected = 4");
writeLine("");

// Archive pool
const poolPath = path.resolve(root, "data", "out", "pools", "residue_pool.json");
if (fs.existsSync(poolPath)) {
  const ts = new Date().toISOString().replace(/[:.]/g, "-");
  const bak = path.resolve(root, "data", "out", `residue_pool.${ts}.json`);
  fs.renameSync(poolPath, bak);
}

// Ingest
let countDup = 0;
let countSutured = 0;
let countResidue = 0;
const seenPackets = new Set();

for (const f of files) {
  const uri = `local://result005/${f.name}`;
  const res = runCmd("node", ["dist/cli.js", "ingest", "--file", f.abs, "--uri", uri, "--cycle", "0", "--eps", "0.0001"]);
  if (res.status !== 0) fail(`ingest ${f.name} failed`);
  const j = parseLastJson(res.stdout || "");
  if (!j || !j.packet_id || !j.status) fail(`ingest ${f.name} missing JSON output`);
  if (seenPackets.has(j.packet_id)) {
    countDup++;
  } else if (j.status === "sutured") {
    countSutured++;
  } else {
    countResidue++;
  }
  seenPackets.add(j.packet_id);
}

writeLine("B) Outcomes");
writeLine(`DUPLICATE = ${countDup}`);
writeLine(`SUTURED = ${countSutured}`);
writeLine(`RESIDUE = ${countResidue}`);
writeLine("");

// Round 1
const logsDir = path.resolve(root, "data", "out", "logs");
let res = runCmd("npm", ["run", "round", "--", "--cycle", "1", "--eps", "0.0001", "--scope", "limits-geometry"]);
if (res.status !== 0) fail("round 1 failed");
let round1 = parseLastJson(res.stdout || "");
if (!round1) {
  const roundLog = latestRoundLog(logsDir);
  if (roundLog) round1 = readJson(path.resolve(logsDir, roundLog));
}
if (!round1) fail("round 1 JSON missing");

// Round 2
res = runCmd("npm", ["run", "round", "--", "--cycle", "1", "--eps", "0.0001", "--scope", "limits-geometry"]);
if (res.status !== 0) fail("round 2 failed");
let round2 = parseLastJson(res.stdout || "");
if (!round2) {
  const roundLog = latestRoundLog(logsDir);
  if (roundLog) round2 = readJson(path.resolve(logsDir, roundLog));
}
if (!round2) fail("round 2 JSON missing");

const merges1 = Number(round1.merges ?? 0);
const merges2 = Number(round2.merges ?? 0);

writeLine("C) Round stats");
writeLine(`merges_round1 = ${merges1}`);
writeLine(`merges_round2 = ${merges2}`);
writeLine("");

// Compression
const trace = (round1.trace_sample || []).filter((t) => t.step === "merge");
const phasesSeen = new Set();
let compressionOk = true;

writeLine("D) Compression");
if (trace.length === 0) {
  writeLine("(no merges in trace)");
} else {
  const sample = trace.slice(0, 10);
  for (const t of sample) {
    phasesSeen.add(t.phase);
    const maxBefore = Math.max(t.r_before_a, t.r_before_b);
    const ok = t.r_after < maxBefore;
    if (!ok) compressionOk = false;
    writeLine(`phase=${t.phase} sim=${t.sim} w=${t.w} R_before_a=${t.r_before_a} R_before_b=${t.r_before_b} R_after=${t.r_after} compress=${ok ? "OK" : "FAIL"}`);
  }
}
writeLine("");

writeLine("E) Phases rencontrées");
writeLine(phasesSeen.size ? Array.from(phasesSeen).sort().join(", ") : "none");
writeLine("");

writeLine("F) Idempotence");
writeLine(merges2 === 0 ? "PASS" : "FAIL");
writeLine("");

// Verdict
let verdict = "PASS";
let cause = "";
if (!(merges1 > 0)) {
  verdict = "FAIL";
  cause = "merges_round1 == 0";
} else if (merges2 !== 0) {
  verdict = "FAIL";
  cause = "merges_round2 != 0";
} else if (!compressionOk) {
  verdict = "FAIL";
  cause = "compression check failed";
}

writeLine("G) Verdict final");
if (verdict === "PASS") {
  writeLine("RESULT005: PASS");
} else {
  writeLine(`RESULT005: FAIL (${cause})`);
}
