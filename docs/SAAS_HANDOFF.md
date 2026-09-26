# SaaS handoff notes

## Deployment unit

Deploy AC78 as the core compute service. Treat parser/repair projects as adapters and DD094 as a research workload.

Suggested service split:

```
client
  |
API/auth
  |
ingestion adapter
  |-- consistency-parser
  |-- csv-consistency-repair
  |-- json-consistency-repairer
  |
typed CR envelope
  |
AC78 solver service
  |
receipt store / provenance index
  |
graph/search/UI
```

## Service invariants

The wrapper must preserve:

1. request identity;
2. input hashes;
3. explicit typed fields;
4. AC78 version;
5. all returned receipts;
6. open residuals;
7. zero-truth-credit boundaries;
8. no API-layer promotion to ROOT or formal proof.

## Suggested request envelope

```json
{
  "request_id": "client-generated-id",
  "dataset_id": "optional-dataset-id",
  "records": [],
  "solver_options": {
    "max_waves": 24,
    "max_calls": 100000,
    "stable_waves": 2
  },
  "hypertriangle_request": null
}
```

The adapter owns conversion from records into solver nodes. That conversion should be versioned and auditable.

## Persistence

Persist separately:

- raw upload/object storage;
- normalized deterministic representation;
- CR typed envelope;
- solver result;
- receipt/provenance graph;
- adapter version and solver version.

This makes reruns and disagreement analysis possible.

## Multi-tenant concerns

Before a public SaaS:

- isolate tenant data;
- cap run resources;
- make long runs asynchronous at the application layer;
- keep deterministic run IDs;
- store immutable receipts;
- do not let user-supplied Python execute inside the solver process;
- validate JSON sizes and nesting before ingestion.

## Research namespace

DD094 should be exposed, if at all, under something like `/research/dd094/*`, not mixed into the general CR API.
