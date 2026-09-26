# Embedded CR release artifacts

This directory contains reproducible artifacts for the CR handoff.

## Current engine: AC79

AC79 is reconstructed from the historical AC78 base plus a deterministic 24-part delta.

Base:

`releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz`

Base SHA-256:

`506c7c7ccb5994b8be6a0e239cc2e2c298bf928021a119b6675886b102f89d65`

AC79 delta chunks:

`releases/ac79_delta_b64/00.b64` through `23.b64`

Decoded delta SHA-256:

`f073dee72c96dec623a23cb59cfe5644a97a7abef82db2b2685d3e2bfeb934ac`

Reconstruct and verify:

```bash
python scripts/verify_cr_artifacts.py
python scripts/verify_ac79_delta.py
bash scripts/reconstruct_ac79.sh .ci/ac79
```

The reconstructed tree contains `SHA256SUMS.json` with 926 AC79 file hashes.

## Historical AC78 base

AC78 is retained byte-for-byte as the parent release and rollback/reference point. It is not deleted or silently rewritten.

## Research

`releases/DD094_PASS117_LATEST_RESEARCH_SOURCE_20260925.tar.xz`

SHA-256:

`20320d91932442c04cd873282ddbb0297fce9153998312027fc980d867b653f9`

DD094 is a downstream research package, not a dependency of AC79.
