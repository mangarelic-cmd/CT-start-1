# AC79 — Progress-Aware Fixed-Point Control

## Purpose

AC79 fixes the control failure observed in the AC78 recursive/ALL-AUX path: a run could continue generating structurally equivalent OPEN descendants or wrappers until a resource cap fired even when no new scientific information entered the frontier.

## Control invariant

A continuation is justified only by meaningful progress. AC79 does not treat bookkeeping growth as scientific progress.

Meaningful progress is restricted to:

1. new context-compatible supply;
2. verified proof or refutation;
3. a new reusable material/provider/carrier/relation object;
4. a strict improvement in obligation rank.

## Fixed-point behavior

AC79 fingerprints the scientific state/frontier and terminates when the state stabilizes or cycles without meaningful progress. Resource limits remain available as safety backstops.

## Regression evidence

The supplied anti-loop regression records:

- AC78: 5000 calls, stopped by `RESOURCE_CHECKPOINT_MAX_CALLS`;
- AC79: 2277 calls, stopped by `FIXED_POINT_TERMINAL_LEAF`;
- 2723 fewer calls, a 54.46% reduction in that regression;
- open residuals reduced from 412 to 129;
- final frontier reduced from 113 to 64.

The qualification suite reports 9/9 checks passed. The targeted fixed-point pytest file passes 5/5 locally. The supplied full pytest receipt reports 123 passed and 1 inherited slow exhaustive test deselected.

## Reproducibility

Run:

```bash
python scripts/verify_ac79_delta.py
bash scripts/reconstruct_ac79.sh .ci/ac79
PYTHONPATH=.ci/ac79/02_RUNTIME python -m pytest -q .ci/ac79/03_TESTS/test_ac79_progress_fixed_point.py
PYTHONPATH=.ci/ac79/02_RUNTIME python .ci/ac79/02_RUNTIME/run_ac79_qualification.py
```

The reconstruct step verifies all files listed in AC79's own `SHA256SUMS.json`.
