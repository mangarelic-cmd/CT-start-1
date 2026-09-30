# Dependency inventory, 2026-09-30

## What was already on GitHub

Inventory baseline: `mangarelic-cmd/CT-start-1`, main commit `c7501ad178e1cd545e9ea46677440b98d7efe73d`. All nine then-current branch trees were inspected, along with the three unique embedded release archives identified. The AC82 overlay could not be decoded and is not treated as audited. The repository had one published release (`v0.5.0`) with no attached dependency assets. The default trees of the three other accessible project repositories were also checked; their PASS016 filenames refer to different JSON/parser projects.

- Main already includes `artifacts/releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz`, SHA-256 `506c7c7ccb5994b8be6a0e239cc2e2c298bf928021a119b6675886b102f89d65`, and its declared NumPy/SciPy/SymPy dependencies in `requirements-cr.txt`
- That cumulative AC78 archive contains `sovereign_solver.py`, `all_everything_wave_engine.py`, AC73 state/contract/qualification files and later changes. Presence of those names is **not** proof of byte-identical AC73 behavior
- AC124 is separately available at commit `4bd11dcf7524a7453fdba9445c3a5a72647f9b2a`, path `AC124/`; its four public tests concern the deliberately limited instrumentation slice
- Hyperqubit II and Temporal PASS025 are self-contained public Zenodo archives. They need documented install/run commands rather than substitute research implementations

This is a bounded inventory, not proof that missing originals do not exist in an unexamined historical commit, private account, or author working directory.

## Missing Causal Memory original

Required frozen archive:

- `CAUSAL_MEMORY_CUMULATIVE_PASS016_20260917.zip`
- Published SHA-256: `1db65f27f137c8b260bded8c05074bc78fd2545091264a28804ac7ef71bdaaa0`

The public v2.1 ZIP identifies and hashes this archive but does not include it. Its original 60 core unit tests, 105 proof-audit checks, 17 adversarial tests, and the shared-root codec plus **11 original JSON files** behind the 15,561,243 → 2,700,557-byte claim were not recovered. Generating new JSON data would create a different experiment and would not close this gap.

The public ZIP's distinct generative-coherence benchmark is included unchanged here and can be rerun. `--full-memory` means its ten-row ladder plus scaling, not the missing PASS016 test suite or 11JSON benchmark.

## Missing Alignment inputs

The public V7 builder reads these exact V6 files:

- `FORMAL/CAUSAL_AI_ALIGNMENT_FORMAL_MODEL_V6_FINAL.json`
- `FORMAL/CAUSAL_AI_ALIGNMENT_AXIOM_THEOREM_MAP_V6_FINAL.json`
- `FORMAL/PROOF_STATUS_LEDGER_V6.json`
- `DEMOS/DEMO_RESULTS_V6.json`

Expected parent directory: `CAUSAL_AI_ALIGNMENT_FINAL_V6_20260921`.

The AC73 runner expects the `02_RUNTIME` closure from `SC_SOLVER_AC73_CAUSAL_GRID_ATLAS_CORE_20260921`. Later cumulative lineage records identify the original AC73 ZIP SHA-256 as `e2d9621d6cefea06143708af4e5da8157a0ab992d24fcc5e2ebff42b9b84b531`; the original bytes were not recovered or matched. A later AC77/AC78 runtime must not be silently substituted and labeled AC73 reproduction.

The V7 source adds 16 executable demos to 64 inherited V6 result rows. This runner independently executes those 16 new demos and the finite audit. The unavailable V6 fixture files and AC73 closure prevent claiming an unchanged full release rebuild.

## How to close the remaining gaps

Supply the original frozen archives and their fixtures, verify them against the recorded checksums, inspect redistribution rights and privacy, and add a separate exact-version entrypoint. Preserve the original test semantics. A compatible later solver can be evaluated separately, labeled with its actual version; it does not retroactively establish the historical result.
