import path from "node:path";
import process from "node:process";
import { readText, writeJson } from "./util_fs.js";
import { parseCSL } from "./parser.js";
import { runCVM } from "./cvm.js";

function usage(): void {
  console.log("Usage:");
  console.log("  node dist/cli.js run <input.csl> [out.json]");
  console.log("");
  console.log("Example:");
  console.log("  node dist/cli.js run examples/demo.csl out/test.json");
}

function die(msg: string, code = 1): never {
  console.error(msg);
  process.exit(code);
}

const args = process.argv.slice(2);
if (args.length === 0) {
  usage();
  process.exit(1);
}

const cmd = args[0];

if (cmd === "run") {
  const inPath = args[1];
  if (!inPath) {
    usage();
    die("Error: missing <input.csl>");
  }

  const outPath = args[2] || "out/ct_graph_final.json";

  const cslText = readText(path.resolve(inPath));
  const prog = parseCSL(cslText);

  const result = runCVM(prog);

  writeJson(path.resolve(outPath), result);

  console.log(
    `ct-cvm-mini: converged=${result.converged} i=${Number(result.alignment_index).toFixed(6)} iters=${result.iters}`
  );
} else {
  usage();
  die(`Error: unknown command "${cmd}"`);
}
