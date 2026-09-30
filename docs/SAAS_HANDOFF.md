# SaaS handoff notes

## Deployment unit

Deploy **AC82** as the current CR compute service. Treat parser/repair projects as adapters and DD094 as a research workload.

AC82 adds two execution controls that the API layer must preserve:

1. sovereign ROOT-progress stopping;
2. bulk immutable relation virtualization.

Large immutable pair-relation tables should enter the solver once, become content-addressed evidence banks, and thereafter be referenced by bank ID, provider, pair count and SHA-256. Exact rows remain queryable on demand.

Suggested service split:

```
client
  |
API/auth
  |
ingestion adapter
  |
typed CR envelope
  |
AC82 solver service
  |-- sovereign stop
  |-- bulk evidence vault
  |-- HyperTriangle / 99 ALL-AUX
  |
receipt store / provenance index
  |
graph/search/UI
```

## Service invariants

The wrapper must preserve request identity, input hashes, typed fields, AC82 version, returned receipts, open residuals, evidence-bank digests, zero-truth-credit boundaries, and the rule that API code cannot promote output to ROOT/formal proof.

Resource ceilings remain backstops. Application timeouts must not be interpreted as scientific terminality.
