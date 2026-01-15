import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();
const cvmCli = path.join(root, "ct-cvm-mini", "dist", "cli.js");
const inCsl = path.join(root, "ct-cvm-mini", "examples", "demo.csl");
const outJson = path.join(root, "data", "out", "logs", "tmp_cvm_contract.json");

function run() {
  const outDir = path.dirname(outJson);
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  execFileSync("node", [cvmCli, "run", inCsl, outJson], { stdio: "inherit" });

  const raw = fs.readFileSync(outJson, "utf8");
  const j = JSON.parse(raw);
  const phi = j?.final?.phi || {};
  const keys = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"];
  for (const k of keys) {
    if (!(k in phi)) throw new Error(`missing ${k}`);
    const v = Number(phi[k]);
    if (!Number.isFinite(v)) throw new Error(`non-finite ${k}`);
  }
  console.log("OK cvm_contract_smoke");
}

run();
