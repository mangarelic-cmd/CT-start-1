#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="$ROOT_DIR/artifacts/releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz"
CHUNKS="$ROOT_DIR/artifacts/releases/ac79_delta_b64"
DEST="${1:-$ROOT_DIR/.ci/ac79}"
DELTA="$DEST/.ac79_delta.tar.xz"
EXPECTED_DELTA_SHA="f073dee72c96dec623a23cb59cfe5644a97a7abef82db2b2685d3e2bfeb934ac"

python "$ROOT_DIR/scripts/verify_ac79_delta.py"

rm -rf "$DEST"
mkdir -p "$DEST"

# The repository AC78 artifact is intentionally a compact runtime closure,
# not the complete historical source release.
tar -xJf "$BASE" -C "$DEST"
cat "$CHUNKS"/*.b64 | base64 --decode > "$DELTA"

ACTUAL_DELTA_SHA="$(sha256sum "$DELTA" | awk '{print $1}')"
if [[ "$ACTUAL_DELTA_SHA" != "$EXPECTED_DELTA_SHA" ]]; then
  echo "AC79 delta SHA mismatch: $ACTUAL_DELTA_SHA != $EXPECTED_DELTA_SHA" >&2
  exit 1
fi

tar -xJf "$DELTA" -C "$DEST"
rm -f "$DELTA"

python - "$DEST" <<'PY'
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / "SHA256SUMS.json").read_text(encoding="utf-8"))
entries = {entry["path"]: entry for entry in manifest["files"]}

if manifest.get("schema") != "AC79_RELEASE_MANIFEST_V1":
    raise SystemExit(f"unexpected manifest schema: {manifest.get('schema')!r}")
if manifest.get("file_count") != len(entries):
    raise SystemExit("AC79 manifest file_count mismatch")

required_delta_files = [
    "00_STATE/AC79_STATE.json",
    "01_CONTRACT/AC79_PROGRESS_AWARE_FIXED_POINT_CONTRACT.json",
    "02_RUNTIME/all_everything_wave_engine.py",
    "02_RUNTIME/automation_reconciliation_ac66.py",
    "02_RUNTIME/progress_fixed_point_guard.py",
    "02_RUNTIME/run_ac79_qualification.py",
    "02_RUNTIME/sovereign_solver.py",
    "03_TESTS/test_ac78_hypertriangle_memory_integration.py",
    "03_TESTS/test_ac79_progress_fixed_point.py",
    "06_RECEIPTS/AC79_ANTI_LOOP_COMPARISON.json",
    "06_RECEIPTS/AC79_PARENT_DELTA_RECEIPT.json",
    "06_RECEIPTS/AC79_PYTEST_RECEIPT.json",
    "06_RECEIPTS/AC79_QUALIFICATION_RECEIPT.json",
    "AC79_REPORT_FR.md",
    "RELEASE_AC79.md",
]

def verify(path_text: str) -> None:
    entry = entries.get(path_text)
    if entry is None:
        raise SystemExit(f"AC79 manifest missing required entry: {path_text}")
    path = root / path_text
    if not path.is_file():
        raise SystemExit(f"AC79 runtime reconstruction missing required file: {path_text}")
    data = path.read_bytes()
    if len(data) != entry["size"]:
        raise SystemExit(f"AC79 size mismatch: {path_text}")
    actual = hashlib.sha256(data).hexdigest()
    if actual != entry["sha256"]:
        raise SystemExit(f"AC79 hash mismatch: {path_text}")

for path_text in required_delta_files:
    verify(path_text)

present_verified = 0
for path_text in entries:
    if (root / path_text).is_file():
        verify(path_text)
        present_verified += 1

missing_full_source = len(entries) - present_verified
print(
    "AC79 compact runtime reconstruction integrity PASS: "
    f"{present_verified} present manifest files verified; "
    f"{missing_full_source} inherited full-source-only files intentionally absent"
)
PY

echo "$DEST"
