# CR integration components

The CR handoff intentionally keeps ingestion components modular.

## Existing repositories

### consistency-parser

https://github.com/mangarelic-cmd/consistency-parser

Use for deterministic parsing, structural repair, ambiguity-safe abstention and reusable route maps.

### csv-consistency-repair

https://github.com/mangarelic-cmd/csv-consistency-repair

Use for CSV/multi-file consistency repair before conversion to typed CR records.

### json-consistency-repairer

https://github.com/mangarelic-cmd/json-consistency-repairer

Use for JSON syntax/semantic reconstruction, provenance-aware correction and replay.

### CT-start-1

This repository's original component. Use for deterministic form deduplication, skins and residues.

## Integration rule

Adapters may normalize or repair representation. They do not receive authority to manufacture solver truth, ROOT, theorem identity, or HyperTriangle slot assignment.
