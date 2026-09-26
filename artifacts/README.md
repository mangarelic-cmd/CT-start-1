# Embedded CR release artifacts

This directory contains source archives for the CR handoff.

## Engine

`releases/AC78_HYPERTRIANGLE_CORE_SOURCE_20260925.tar.xz`

SHA-256:

`506c7c7ccb5994b8be6a0e239cc2e2c298bf928021a119b6675886b102f89d65`

This is the production/integration starting point. It contains the full AC78 runtime dependency closure required by the CI smoke test, together with the frozen HyperTriangle provider.

## Research

`releases/DD094_PASS117_LATEST_RESEARCH_SOURCE_20260925.tar.xz`

SHA-256:

`20320d91932442c04cd873282ddbb0297fce9153998312027fc980d867b653f9`

DD094 is a downstream research package, not a dependency of AC78.

Run `python scripts/verify_cr_artifacts.py` after cloning.
