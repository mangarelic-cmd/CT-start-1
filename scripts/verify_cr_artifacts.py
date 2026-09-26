#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    ROOT / "artifacts" / "releases" / "AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz":
        "506c7c7ccb5994b8be6a0e239cc2e2c298bf928021a119b6675886b102f89d65",
    ROOT / "artifacts" / "releases" / "DD094_PASS117_LATEST_RESEARCH_SOURCE_20260925.tar.xz":
        "20320d91932442c04cd873282ddbb0297fce9153998312027fc980d867b653f9",
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> None:
    failed = False
    for path, expected in EXPECTED.items():
        if not path.is_file():
            print(f"MISSING {path}")
            failed = True
            continue
        actual = sha256(path)
        if actual != expected:
            print(f"FAIL {path.name} {actual} != {expected}")
            failed = True
        else:
            print(f"OK {path.name} {actual}")
    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
