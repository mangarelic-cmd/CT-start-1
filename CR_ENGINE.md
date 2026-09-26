# CR Engine handoff — 2026-09-25

This repository includes a reproducible handoff for the current Causal Resolution (CR) engine line.

## Current master engine

**SC_SOLVER AC78** is the current master solver package.

AC78 extends the autonomous AC77 solver with the frozen **HyperTriangle Solver AUX v1.0.0**. HyperTriangle is a verified pre-ALL-AUX provider; it does not replace or inflate the 99 ALL-AUX mechanisms.

Core direction:

```
typed data
  -> fixed invariant / causal slot
  -> 144-slot memory
  -> declared activation contract
  -> typed HyperTriangle capability
  -> receipt / provenance
  -> solver continuation
```

Authority boundary:

- HyperTriangle truth credit: 0
- ROOT write capability: NONE
- RETURN write capability: NONE
- solver mutation capability: NONE
- AUX terminality is not scientific ROOT
- no implicit fuzzy assignment of arbitrary data to F001-F144

## Production vs research

### Production / integration target

`artifacts/releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz`

This is the package to use as the starting CR engine for a SaaS wrapper. The embedded compact source contains the complete AC78 runtime dependency closure, contracts/state, and the frozen HyperTriangle provider needed for the included smoke test.

### Research module

`artifacts/releases/DD094_PASS117_LATEST_RESEARCH_SOURCE_20260925.tar.xz`

DD094 is a downstream cosmology/research program. It is **not** the solver and is not required to deploy AC78. Keep it under a research namespace or feature flag.

## Verify the embedded releases

```bash
python scripts/verify_cr_artifacts.py
```

Extract:

```bash
mkdir -p dist/ac78
tar -xJf artifacts/releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz -C dist/ac78

mkdir -p dist/dd094
tar -xJf artifacts/releases/DD094_PASS117_LATEST_RESEARCH_SOURCE_20260925.tar.xz -C dist/dd094
```

Install the current runtime dependencies:

```bash
python -m pip install -r requirements-cr.txt
```

## Minimal AC78 use

```python
import sys
sys.path.insert(0, "dist/ac78/02_RUNTIME")

from sovereign_solver import SovereignSolver

solver = SovereignSolver()

capabilities = solver.hypertriangle({
    "request_id": "example-capabilities",
    "mode": "capabilities",
    "payload": {}
})

print(capabilities)
```

For normal solver work use `SovereignSolver.solve_universal(...)`. HyperTriangle is invoked only by an explicit typed request.

## SaaS handoff

Start with:

- `docs/CHAD_START_HERE.md`
- `docs/SAAS_HANDOFF.md`
- `integrations/README.md`
- `research/dd094/README.md`

The first service surface should stay thin: health/capabilities, typed ingestion, solve, and HyperTriangle. Do not add semantic authority in the API layer.

## Existing ingestion / repair components

Separate repositories under the same GitHub account:

- https://github.com/mangarelic-cmd/consistency-parser
- https://github.com/mangarelic-cmd/csv-consistency-repair
- https://github.com/mangarelic-cmd/json-consistency-repairer

These are useful ingestion-side preprocessors and should remain separate services/libraries rather than being copied into solver core.

## Release identifiers

- AC78 full solver release SHA-256: `0b07684db8c5716d96ea047464430b8a463d119a6f385ed13c069286333c5b3a`
- HyperTriangle AUX frozen v1.0.0 SHA-256: `fa82b76a200703afe38e1f3e6ecabe2b1cb363f4fbb89c34ca00adf24ea23295`
- Embedded complete AC78 source artifact SHA-256: `506c7c7ccb5994b8be6a0e239cc2e2c298bf928021a119b6675886b102f89d65`
- Embedded compact DD094 PASS117 research artifact SHA-256: `20320d91932442c04cd873282ddbb0297fce9153998312027fc980d867b653f9`
