# Chad — start here

The shortest useful path to a CR SaaS proof of concept is:

1. Materialize and extract the AC78 package.
2. Wrap `SovereignSolver` behind a small stateless API.
3. Keep ingestion adapters outside the solver.
4. Preserve every solver receipt and open residual as first-class output.
5. Add DD094 only as a research workload after the engine service is running.

## First API surface

Recommended endpoints:

- `GET /v1/health`
- `GET /v1/capabilities`
- `POST /v1/ingest`
- `POST /v1/solve`
- `POST /v1/hypertriangle`

The API should add transport/auth/storage only. It should not invent solver semantics.

## Dataset ingestion

CR should not be sold as “an ontology generator” in the ordinary sense. A dataset can be transformed into typed observations/problems and processed through the solver; the resulting structures, residues, routes, constraints and receipts can then be exposed as an ontology-like graph.

Safe pipeline:

```
raw dataset
 -> parser / format repair
 -> deterministic normalization
 -> typed CR records
 -> AC78
 -> receipts + unresolved currents + provenance
 -> graph/index/API representation
```

Do not silently map arbitrary raw fields to HyperTriangle F001-F144 slots. AC78 intentionally requires explicit typed HyperTriangle requests.

## Existing components worth connecting

- `consistency-parser`: generic parsing / structural repair
- `csv-consistency-repair`: CSV consistency and multi-file repair
- `json-consistency-repairer`: JSON consistency repair and replay
- `CT-start-1`: deterministic form deduplication / residue preservation
- `AC78`: solver core
- `DD094 PASS117`: research consumer, not production dependency

## What not to expose as product claims

- AUX terminality is not scientific truth.
- Structural receipts do not become ROOT merely because a run completed.
- DD094 remains research.
- Collatz material is not to be represented as a proof.
- Photonic work is not included in this handoff.

## Immediate POC

A practical first POC is: upload a JSON/CSV dataset, normalize it through the existing repairer, convert rows/records into typed CR inputs, run AC78, and return:

- normalized input hash
- solver version
- mechanism counts
- HyperTriangle receipts when explicitly requested
- open residuals
- provenance hashes
- solution/formal-proof flags

That gives a SaaS team a stable interface without overstating what the engine has certified.
