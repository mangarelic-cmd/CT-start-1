// File: src/cli.ts
// Purpose: Start-1 CLI (ingest + round). Dependency-safe with pipeline.ts and round.ts.

import path from "node:path";
import fs from "node:fs";
import { ingestFile } from "./pipeline.js";
import { runRound } from "./round.js";

type Scope = string;

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

function requireNumber(name: string): number {
  const v = arg(name);
  if (v === undefined) throw new Error(`Missing required ${name}`);
  const n = Number(v);
  if (!Number.isFinite(n)) throw new Error(`Invalid number for ${name}: ${v}`);
  return n;
}

/**
 * Start-1 rule: rounds are event-driven.
 * Scope is allowed only as operational batching label (not causal law).
 */
function getScope(): Scope {
  const v = arg("--scope");
  if (!v) return "event";
  return v;
}

async function main() {
  const cmd = process.argv[2];

  if (!cmd) {
    console.log("Usage:");
    console.log("  node dist/cli.js ingest --file <path> --uri <uri> --cycle <n> --eps <eps_son>");
    console.log("  node dist/cli.js round  --cycle <n> --eps <eps_son> [--scope <label>]");
    process.exit(1);
  }

  if (cmd === "help" || cmd === "--help" || cmd === "-h") {
    console.log("Usage:");
    console.log("  node dist/cli.js ingest --file <path> --uri <uri> --cycle <n> --eps <eps_son>");
    console.log("  node dist/cli.js round  --cycle <n> --eps <eps_son> [--scope <label>]");
    process.exit(0);
  }

  if (cmd === "ingest") {
    const file = arg("--file");
    const uri = arg("--uri") ?? "local://unknown";
    if (!file) throw new Error("Missing --file");

    const cycle_depth = requireNumber("--cycle");
    const eps_son = requireNumber("--eps");

    const abs = path.resolve(file);
    if (!fs.existsSync(abs)) throw new Error("File not found: " + abs);

    const root = path.resolve(".");
    const out = await ingestFile({ file: abs, uri, root, cycle_depth, eps_son });
    console.log(JSON.stringify(out, null, 2));
    return;
  }

  if (cmd === "round") {
    const cycle_depth = requireNumber("--cycle");
    const eps_son = requireNumber("--eps");
    const scope = getScope();
    const root = path.resolve(".");
    const out = await runRound({ root, cycle_depth, eps_son, scope });
    console.log(JSON.stringify(out, null, 2));
    return;
  }

  console.log("Unknown command:", cmd);
  console.log("Usage:");
  console.log("  node dist/cli.js ingest --file <path> --uri <uri> --cycle <n> --eps <eps_son>");
  console.log("  node dist/cli.js round  --cycle <n> --eps <eps_son> [--scope <label>]");
  process.exit(1);
}

main().catch((e: unknown) => {
  console.error(e);
  process.exit(1);
});
