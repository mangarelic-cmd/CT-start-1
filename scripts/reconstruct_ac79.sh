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
manifest_path = root / "SHA256SUMS.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
entries = manifest["files"]

if manifest.get("schema") != "AC79_RELEASE_MANIFEST_V1":
    raise SystemExit(f"unexpected manifest schema: {manifest.get('schema')!r}")
if manifest.get("file_count") != len(entries):
    raise SystemExit("AC79 file_count mismatch")

for entry in entries:
    path = root / entry["path"]
    if not path.is_file():
        raise SystemExit(f"AC79 missing reconstructed file: {entry['path']}")
    data = path.read_bytes()
    if len(data) != entry["size"]:
        raise SystemExit(f"AC79 size mismatch: {entry['path']}")
    actual = hashlib.sha256(data).hexdigest()
    if actual != entry["sha256"]:
        raise SystemExit(f"AC79 hash mismatch: {entry['path']}")

print(f"AC79 reconstruction integrity PASS: {len(entries)} files")
PY

echo "$DEST"
