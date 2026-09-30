# Validation of this packaging change

Executed 2026-09-30 UTC in a fresh Python virtual environment on Linux x86_64, Python 3.12.14. Installed this directory's requirements: NumPy 2.3.5, Brotli 1.2.0, lz4 4.4.5, pytest 9.1.1. System Zstandard CLI: 1.5.7.

## Executed checks

- Eight wrapper/safety unit tests: PASS
- Seven vendored source/result files: SHA-256 and size verified, independently compared byte-for-byte against the original public ZIP members
- `run.py --full-memory`: PASS, about 185 seconds in this environment
  - Ten freshly generated 8,000,000-byte ladder inputs; raw hashes and causal retained sizes matched the public fixtures
  - Causal sizes: 8,000,000; 7,300,088; 6,125,088; 4,125,088; 2,125,088; 900,088; 92,887; 9,963; 1,104; 88 bytes
  - Four perfect-coherence scaling rows: 88-byte capsules, exact replay verified
  - Seven conventional codecs actually compressed/decompressed each ladder input
  - Three supplied temporary-source deletion and capsule-corruption checks passed
  - Alignment: 16/16 new demos passed; freshly enumerated 248,832-state audit equaled the public audit JSON, including 32 accepted configurations and zero forbidden witnesses
- A clean export of the staged Git tree, without any surrounding source directories: eight unit tests and default `run.py` PASS; approximately 26 seconds for the quick run
- Optional downloader: exact local release archives for both projects extracted safely into new directories; an additional fresh HTTPS Temporal download passed the pinned SHA-256 and extracted 527 entries
- Optional Temporal command sequence on the clean extracted release: 386 tests passed; example PASS010 ran; PASS025 benchmark returned 10/10 checks and 33,867 relations
- Optional Hyperqubit command on the clean extracted release: 42/42 assertion groups passed
- No credential-pattern findings in newly added files. Only the public source subset, its public baselines, scoped wrappers and documentation are included
- `git diff --check`: PASS

The full-path packaging test caught and corrected an initial wrapper assumption: the frozen Memory release stores scaling fixtures in `scaling.json`, separately from `results.json`. Both originals are now included unchanged and the fixture schema/counts have a regression test.

## Boundaries

The 88-byte capsule excludes shared decoder and installed runtime dependencies. Timings are observations, not a controlled performance comparison. Recorded checks are computational tests, not external scientific validation.

The unavailable original PASS016/11JSON and V6/AC73 inputs listed in [DEPENDENCIES.md](DEPENDENCIES.md) were not regenerated or substituted. The full historical research suite is not claimed. Optional Temporal/Hyperqubit tests are distinct from the eight packaging tests and from the scoped Alignment checks.

GitHub Actions has its own independently visible result after publication; this report records the local checks above and does not assert a future CI outcome.
