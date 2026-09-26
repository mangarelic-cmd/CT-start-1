# CR Engine handoff — 2026-09-26

## Current master engine

**SC_SOLVER AC82 — Bulk Evidence Vault + Sovereign Stop + HyperTriangle Core** is the current master solver handoff.

AC82 supersedes AC78/AC79/AC81 for integration. It preserves the AC77 metrology and AC78 HyperTriangle provider surface, keeps the AC81 sovereign ROOT-progress stop rule, and adds bulk evidence virtualization for evidence-rich workloads.

### What AC82 fixes

AC81 stopped recursive re-wave loops, but a global packet containing the 6,903 PASS054 pair relations could still spend excessive time inside one ALL-AUX wave because the same immutable relation table was repeatedly serialized and hashed.

AC82 content-addresses large immutable relation tables once into a solver-local evidence vault. Broadcast nodes carry only:

- `relation_bank_id`
- exact pair count
- provider
- SHA-256
- on-demand query handle

Exact relation rows remain queryable through `bulk_relation_query(...)`. This is execution infrastructure only and adds **zero truth credit**.

### Stop semantics retained

- resolved input: one bounded complete ALL-AUX enrichment wave, then `COMPLETE_BOUNDED_ENRICHMENT`;
- open sovereign ROOT requirements: re-wave only after exact ROOT payment or strict obligation-rank descent;
- otherwise: `FIXED_POINT_ROOT_NO_PROGRESS`;
- `max_calls` / `max_waves` remain emergency backstops.

## Reproducible repository handoff

The repository keeps the historical AC78 compact source archive as the base:

`artifacts/releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz`

AC82 is supplied as an exact overlay:

`artifacts/releases/AC82_FROM_AC78_OVERLAY_20260926.tar.xz`

Overlay SHA-256:

`00a7adcc0f00f370667f041e3c82add64b6ac8e42a722abbf44321fc693257fc`

The user-supplied full AC82 package inspected for this handoff had SHA-256:

`dbd7969a0125cff16afab1967f5492d3a4f5da52f9cc2760755584c8f7c59cea`

## Qualification performed before publication

Targeted regression qualification on the supplied AC82 package:

```
12 passed
```

Covered:

- AC79 progress-aware fixed point;
- AC81 sovereign stop;
- AC82 bulk evidence vault.

The supplied AC82 state declares `QUALIFIED`, `bulk_relation_vault=true`, `sovereign_stop=true`, and `truth_credit_added=0`.

## Reconstruction

```bash
mkdir -p .ci/ac82
tar -xJf artifacts/releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz -C .ci/ac82
tar -xJf artifacts/releases/AC82_FROM_AC78_OVERLAY_20260926.tar.xz -C .ci/ac82
```

Then run the AC79/AC81/AC82 regression tests from the reconstructed tree.

## Authority boundary

- HyperTriangle truth credit: 0
- AC79/AC81/AC82 control logic truth credit: 0
- evidence-vault virtualization truth credit: 0
- ROOT write capability: NONE
- RETURN write capability: NONE
- solver mutation capability from HyperTriangle: NONE

AC82 changes execution and stopping behavior; it does not manufacture theorem truth or physical truth.
