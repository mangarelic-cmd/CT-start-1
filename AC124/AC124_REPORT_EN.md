# AC124 — Theorem-use event instrumentation and route-role adapter

## Verdict

AC124 keeps `67 -> 67`, zero payments and `512 -> 512` macro candidates. It intentionally modifies two inherited runtime components: the proof reconstruction orchestrator and solver world flags. No other parent file is changed.

## Runtime instrumentation

The reconstruction engine now emits a `PROBLEM_APPLICATION_THEOREM_USE_EVENT` only after a proof edge carrying a `theorem_use` declaration has actually verified. Theorem-fabric search candidates, isolated schema proofs, and unverified edges emit no event.

A complete event carries `root_problem_id`, `route_occurrence_id`, `theorem_id`, `theorem_authority_id`, `route_step_index`, `route_provenance`, and `required_role`. The role is accepted only through `EXACT_TYPED_ROUTE_ROLE` authority or an exact `PASS050_ROUTE_ROLE_CONTRACT_V1`.

## PASS050 calibration

The 192 frozen PASS050 contexts are replayed strictly as calibration. The new event adapter round-trips `192/192` to exactly the same `P###/F###`. A live positive T003 calibration emits a verified LOCALIZATION event and recovers `P004/F004`.

## Firewalls and T074

Theorem-fabric search emits zero application events; an unverified proof edge also emits zero. The inherited corpus still contains zero exact T074 problem-application events. A synthetic complete T074 event still returns `FAIL_CLOSED_UNBOUND_THEOREM_ROUTE_PROVIDER`, proving that instrumentation itself creates no PASS050 context.

## Next delta

The next pass must replay or produce real problem routes containing theorem applications, backfill genuine theorem-use events where replay evidence exists, and compile occurrence semantics to exact typed PASS050 roles. Recommended: `AC125_TPTX_REPLAYABLE_PROBLEM_ROUTE_THEOREM_USE_BACKFILL_AND_ROLE_SEMANTICS_COMPILER`.
