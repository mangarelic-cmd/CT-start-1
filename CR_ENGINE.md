# CR Engine handoff — 2026-09-26

This repository carries the reproducible handoff for the current Causal Resolution (CR) engine line.

## Current master engine

**SC_SOLVER AC79 — Progress-Aware Fixed-Point HyperTriangle Core** is the current master solver package.

AC79 is a control-layer successor to AC78. It preserves the AC78 scientific/provider identities and adds a progress-aware fixed-point guard so OPEN wrappers, replay descendants, and equivalent frontier states are not mistaken for new scientific progress.

Core direction:

```
typed data
  -> fixed invariant / causal slot
  -> 144-slot memory
  -> declared activation contract
  -> typed HyperTriangle capability
  -> meaningful-progress guard
  -> fixed-point / cycle detection
  -> receipt / provenance
  -> solver continuation or scientific stop
```

### Meaningful progress

AC79 counts progress only when at least one of the following changes materially:

- context-compatible supply;
- verified proof or refutation;
- reusable material/provider/carrier/relation object;
- strictly improved obligation rank.

Equivalent wrappers, replayed OPEN descendants, and repeated scientific frontiers do not reset convergence.

### Normal stop conditions

The control layer can terminate normally when:

- terminal leaves remain without available supply;
- a complete wave produces no meaningful state change;
- the exact progress/frontier state repeats;
- a non-adjacent state cycle is detected.

Resource limits remain emergency backstops rather than the normal scientific stop condition.

## Reproducible repository packaging

AC78 remains in the repository as the immutable historical base artifact:

`artifacts/releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz`

The repository handoff reconstructs the AC79 runtime closure as a deterministic delta over that byte-stable compact AC78 base. The supplied full AC79 package remains the authority for the complete 926-file source manifest:

`artifacts/releases/ac79_delta_b64/00.b64 ... 23.b64`

Reconstruct AC79 with:

```bash
bash scripts/reconstruct_ac79.sh .ci/ac79
```

The concatenated, decoded AC79 delta is `AC79_DELTA_FROM_AC78_20260926.tar.xz` with SHA-256:

`f073dee72c96dec623a23cb59cfe5644a97a7abef82db2b2685d3e2bfeb934ac`

The originally supplied AC79 ZIP has SHA-256:

`fcf5d778729950efa2bf56212f4a119a1d4c2baab6eb7a591cb81f654fa8acac`

A deterministic standalone AC79 source archive produced during qualification has SHA-256:

`a504a1ecae81f245321e77c0a96706b3e06091c5360d0bc2adedca22384a1c8a`

## Qualification evidence

Local qualification of the supplied full AC79 package:

- release manifest integrity: **926/926 files verified**;
- targeted AC79 fixed-point tests: **5/5 passed**;
- AC79 qualification receipt: **9/9 checks passed**;
- delivered pytest receipt: **123 passed, 1 deselected**;
- the deselected test is the inherited slow AC75 exhaustive compiler campaign.

Anti-loop comparison recorded by AC79:

| Metric | AC78 | AC79 |
| --- | ---: | ---: |
| execution calls | 5000 | 2277 |
| stop state | RESOURCE_CHECKPOINT_MAX_CALLS | FIXED_POINT_TERMINAL_LEAF |
| known nodes | 620 | 325 |
| open residuals | 412 | 129 |
| final frontier | 113 | 64 |
| calls saved | — | 2723 |
| call reduction | — | 54.46% |

Receipt verdict:

`AC79_TERMINATES_BY_SCIENTIFIC_FIXED_POINT_BEFORE_RESOURCE_BACKSTOP`

These are qualification results for the supplied regression scenario; they are not a claim that every future workload will terminate in 2277 calls.

## Authority boundary

The AC78 HyperTriangle authority boundary is preserved:

- HyperTriangle truth credit: 0;
- ROOT write capability: NONE;
- RETURN write capability: NONE;
- solver mutation capability: NONE;
- AUX terminality is not scientific ROOT;
- no implicit fuzzy assignment of arbitrary data to F001-F144.

## CI verification

The repository workflow now:

1. verifies the historical embedded artifact hashes;
2. verifies the 24-part AC79 delta and its SHA-256;
3. reconstructs AC79 from AC78 + delta;
4. verifies every file present in the compact AC79 runtime reconstruction against AC79's full-source `SHA256SUMS.json`, including every AC79 delta file;
5. runs the targeted AC79 fixed-point tests;
6. runs the AC79 qualification program.

## SaaS handoff

Start with:

- `docs/CHAD_START_HERE.md`
- `docs/SAAS_HANDOFF.md`
- `docs/AC79_PROGRESS_AWARE_FIXED_POINT.md`
- `integrations/README.md`
- `research/dd094/README.md`

The API layer should remain thin and preserve the solver's explicit authority boundaries and receipts.

## Existing ingestion / repair components

Separate repositories under the same GitHub account:

- https://github.com/mangarelic-cmd/consistency-parser
- https://github.com/mangarelic-cmd/csv-consistency-repair
- https://github.com/mangarelic-cmd/json-consistency-repairer

These remain ingestion-side preprocessors rather than being copied into solver core.
