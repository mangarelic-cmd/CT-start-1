#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNK_DIR = ROOT / "artifacts" / "releases" / "ac79_delta_b64"
EXPECTED_PARTS = [f"{i:02d}.b64" for i in range(24)]
EXPECTED_SHA256 = "f073dee72c96dec623a23cb59cfe5644a97a7abef82db2b2685d3e2bfeb934ac"

def main() -> None:
    actual_parts = sorted(p.name for p in CHUNK_DIR.glob("*.b64"))
    if actual_parts != EXPECTED_PARTS:
        raise SystemExit(f"AC79 delta chunk set mismatch: {actual_parts}")

    encoded = "".join((CHUNK_DIR / name).read_text(encoding="utf-8").strip() for name in EXPECTED_PARTS)
    try:
        payload = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise SystemExit(f"AC79 delta base64 decode failed: {exc}") from exc

    actual = hashlib.sha256(payload).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"AC79 delta SHA-256 mismatch: {actual} != {EXPECTED_SHA256}")

    print(f"OK AC79 delta parts={len(EXPECTED_PARTS)} bytes={len(payload)} sha256={actual}")

if __name__ == "__main__":
    main()
