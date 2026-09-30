# AC124 — Public technical entrypoint

This directory publishes the code-facing AC124 entrypoint from the Causal Solution cumulative AC124 snapshot.

AC124 is a **fail-closed theorem-use instrumentation and route-role adapter pass**. Its purpose is deliberately narrow: a theorem search result is not promoted to a real theorem-use event, and a theorem-use event is not promoted to a contextual PASS050 binding without the required typed authority.

## Exact AC124 status

- Parent: AC123
- ROOT: `67 -> 67`
- Macro candidate volume: `512 -> 512`
- Runtime theorem-use instrumentation: active
- Emission gate: `VERIFIED_PROOF_EDGE_ONLY`
- Frozen PASS050 event-adapter calibration: `192/192 PASS`
- Search candidate event count: `0`
- Unverified proof-edge event count: `0`
- Inherited real T074 problem-application events: `0`
- New PASS050 bindings: `0`
- Payments: `0`
- Selected AC124→AC114 regression replay: `87 passed, 0 failed`

The next declared pass is:

`AC125_TPTX_REPLAYABLE_PROBLEM_ROUTE_THEOREM_USE_BACKFILL_AND_ROLE_SEMANTICS_COMPILER`

## Core invariant

```text
THEOREM_SEARCH_CANDIDATE != THEOREM_USE_EVENT
SCHEMA_PROOF_OCCURRENCE != PROBLEM_APPLICATION_THEOREM_USE_EVENT
BACKEND_AFFINITY != REQUIRED_ROLE
THEOREM_ID != PASS050_POSITION
THEOREM_USE_EVENT != PASS050_BINDING
```

Only a verified proof application carrying explicit theorem-use provenance can emit a problem-local theorem-use event. A route role becomes bindable only through exact typed route-role authority.

## Small runnable public test

The public slice contains the exact AC124 theorem-use event instrumenter plus a dependency-light test:

```bash
python -m pip install pytest
pytest -q AC124/tests/test_public_instrumentation.py
```

This public test checks:

- verified proof edge -> event emission;
- unverified proof edge -> no event;
- direct role without typed authority -> fail closed;
- deterministic event identity for identical canonical input.

## Scope

The full cumulative AC124 working snapshot is substantially larger than this GitHub entrypoint and contains historical runtime, theorem fabric, fixtures, receipts, provider tables and embedded source evidence. This directory intentionally exposes the AC124 mechanism, contract, release status and selected receipts without pretending that a compact public slice is the complete historical corpus.

Local source archive used for this publication:

- `CAUSAL_SOLUTION_SOFTWARE_ENCYCLOPEDIA_CUMULATIVE_PASS001_R50_20260929.tar.zst`
- local archive SHA-256: `34b116e39b86a3a323a6e2120cf9a78ffc1b2ecb7c8519c3d8686955e23999b9`
- extracted AC124 tree observed locally: 2,084 files / ~76 MB
- AC124 manifest SHA-256: `780ce85a91ea88b995222ade3739110c8a113914e48e465ef11ae238932746f8`
- AC124 manifest summary: 1,984 manifested files; parent file count 1,959

## Research references

- Causal Solution Software Encyclopedia: https://zenodo.org/records/22923146
- Causal AI Alignment: https://zenodo.org/records/22881040

## Claim ceiling

AC124 does **not** claim a universal solver proof, universal scientific truth, or a completed deterministic AI. It demonstrates a scoped engineering rule: application evidence, authority, contextual binding and scientific credit remain separate, and missing authority remains explicit rather than being inferred from search, similarity or naming.
