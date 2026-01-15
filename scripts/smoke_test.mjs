import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = path.resolve(".");
const run = (args, opts = {}) => {
  execFileSync("node", args, { stdio: "inherit", ...opts });
};

const fail = (msg) => {
  console.error(msg);
  process.exit(1);
};

try {
  run([path.join(root, "dist", "cli.js"), "--help"]);

  const inbox = path.join(root, "data", "inbox");
  fs.mkdirSync(inbox, { recursive: true });
  const smokePath = path.join(inbox, "codex_smoke_1.txt");
  const lines = [
    "Line 1: alpha",
    "Line 2: beta",
    "Line 3: gamma",
    "Line 4: delta",
    "Line 5: epsilon",
  ];
  fs.writeFileSync(smokePath, lines.join("\n") + "\n", "utf8");

  run([
    path.join(root, "dist", "cli.js"),
    "ingest",
    "--file",
    smokePath,
    "--uri",
    "codex://smoke/1",
    "--cycle",
    "1",
    "--eps",
    "1",
  ]);

  const expectCycleReject = (cycleVal) => {
    try {
      run([
        path.join(root, "dist", "cli.js"),
        "ingest",
        "--file",
        smokePath,
        "--uri",
        "codex://smoke/1",
        "--cycle",
        String(cycleVal),
        "--eps",
        "1",
      ]);
      fail(`policy decision required: cycle=${cycleVal} accepted (expected rejection)`);
    } catch {
      // Expected failure (cycle < 1 should be rejected).
    }
  };

  expectCycleReject(0);
  expectCycleReject(-1);

  run([
    path.join(root, "dist", "cli.js"),
    "round",
    "--cycle",
    "1",
    "--eps",
    "1",
    "--scope",
    "event",
  ]);

  const tmpOut = path.join(root, "data", "out", "logs", "tmp_cvm_out.json");
  if (fs.existsSync(tmpOut)) {
    const raw = fs.readFileSync(tmpOut, "utf8").trim();
    if (!raw) fail(`Empty tmp_cvm_out.json at ${tmpOut}`);
    const parsed = JSON.parse(raw);
    const phi = parsed?.final?.phi;
    const keys = ["PI", "SQRT2", "SQRT3", "PHI", "LN5"];
    if (!phi || typeof phi !== "object") {
      fail(`Missing final.phi in ${tmpOut}`);
    }
    const actual = Object.keys(phi);
    const missing = keys.filter((k) => !actual.includes(k));
    const extras = actual.filter((k) => !keys.includes(k));
    if (missing.length || extras.length) {
      fail(
        `Invalid final.phi keys in ${tmpOut} missing=${missing.join(",")} extras=${extras.join(",")}`
      );
    }
    for (const k of keys) {
      const v = phi[k];
      if (typeof v !== "number" || !Number.isFinite(v)) {
        fail(`Invalid final.phi.${k} in ${tmpOut}`);
      }
    }
  }

  process.exit(0);
} catch (e) {
  const msg = e instanceof Error ? e.message : String(e);
  fail(`Smoke test failed: ${msg}`);
}
