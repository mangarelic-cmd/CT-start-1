# START-1_CONTRACT (CT)  Causal Deduplication by Form

## 0) Status
This document is the constitutional contract for **Start-1**.
Start-1 must obey these rules. Any deviation is a protocol violation.

---

## 1) Scope and Purpose (Non-Negotiable)

**Start-1 is a form deduplication instrument.**
It compares **forms** (geometries), not meanings.

Start-1 exists to:
1) remove redundant symmetry,
2) extract stable form representatives (skins),
3) preserve and re-process non-fusable matter (residue) until stable.

Start-1 must NOT:
- judge truth,
- interpret semantics,
- produce meaning scores,
- act as a truth engine.

---

## 2) Core Objects

### 2.1 Packet
A Packet is the raw, append-only record of an ingested input.
Packet must be immutable after creation.

### 2.2 Skin
A Skin is a stable **canonical form** representing a deduplicated structure.
A Skin is integrable and may absorb future inputs.

### 2.3 Residue
Residue is **not an error**.
Residue is matter that is currently non-fusable or not yet neighbored.
Residue must be preserved and re-compared over time.

### 2.4 Residue Pool
The residue pool is persistent storage of residues and their clusters/attractors.
Pool is a live system: new residues may trigger new fusions among older residues.

---

## 3) Input/Output Contract

### 3.1 Input
Start-1 ingests raw data (typically text) and treats it strictly as geometry.

### 3.2 Output States (Only these three)
- **DUPLICATE**: exact identity match; no further measurement required.
- **SUTURED**: integrated into an existing structure / forms a stable Skin.
- **RESIDUE**: stored in residue pool for future rounds.

Start-1 must not output any of:
- truth labels,
- semantic explanations,
- probabilistic claims.

---

## 4) Canonical Invariance Rules

Start-1 must be invariant under superficial symmetry:
- normalization (unicode, accents/case/spacing),
- benign punctuation variation,
- line breaks.

This invariance must be deterministic and idempotent.

---

## 5) Identity First (Hard Dedup)

**Rule:** If identity is known duplicate, dedup occurs immediately.

- Compute deterministic packet identity (hash/ID).
- If that identity is already present, return **DUPLICATE** and stop.
- No CVM computation is allowed in this case.

---

## 6) Form Signature and Distance

### 6.1 Form Signature
Start-1 maps each input to a stable form signature (e.g., Vector5).
This signature is used only for:
- indexing,
- distance computation,
- clustering,
- deterministic merging.

### 6.2 Distance
Start-1 must define a deterministic distance function:
d(A,B) -> nonnegative real.

No global dataset statistics are allowed to redefine per-item meaning.
(Example forbidden: normalizing an item by median of other items.)

---

## 7) 118 Slots = Addresses, Not Meanings

Start-1 may implement 118 slots as discrete attractor addresses for clustering.

**Slots are not semantic labels.**
A slot is an address in form-space:
- "belongs to slot 001" is allowed,
- "is Hydrogen" is not allowed at Start-1.

Slots are used to stabilize indexing and clustering, not to interpret content.

---

## 8) Event-Driven Rounds (No Calendar Laws)

### 8.1 Trigger
Rounds are **event-driven**:
- triggered by arrival of a new residue, OR
- triggered by creation of a composite residue after a merge.

Calendar batching (daily/monthly) is permitted only as an operational scheduler,
and must never change causal logic.

### 8.2 Round Definition
A round is a sequence of residue-residue comparisons and merges.

Typical depth: 34 passes (bounded) to avoid forced fusion.
Stop condition: no merge is possible without increasing dissipation.

---

## 9) Merge Rule = Proximity AND Gain (Activation Barrier)

A merge is allowed ONLY if BOTH conditions hold:

### 9.1 Proximity condition
d(Ra, Rb) <= eps

### 9.2 Minimal gain condition (activation barrier / friction)
E(before) - E(after) >= I"_min

Where:
- E(.) is the internal objective/energy (deterministic),
- I"_min is a fixed threshold (may be Son-linked),
- merges without sufficient gain are forbidden.

This prevents over-merging and preserves stable differences.

---

## 10) Residue is First-Class

Residue must never be treated as dead.
Every new residue may unlock merges among older residues.
Pool reprocessing is mandatory under the event-driven rule.

---

## 11) Determinism and Reproducibility

- Same input + same code + same constants => same decisions.
- Output IDs may differ only where explicitly ledger-based (timestamps),
  but the dedup decisions must remain invariant.
- No hidden randomness unless seeded and logged deterministically.

---

## 12) Forbidden Failure Mode: Flatline Scoring

Any scalar score that saturates to a constant across diverse inputs
(e.g., 0.999975 for everything) is considered a measurement failure.

Start-1 must never rely on a saturated scalar to decide dedup.
Dedup decisions must be grounded in identity + distance + merge rule.

---

## 13) Boundary of Start-1 vs Start-2/Start-3

Start-1 ends when:
- the input is deduped (DUPLICATE/SUTURED), OR
- residue is stored and stabilized after bounded event-driven passes.

Start-2 (correction) may operate after Start-1, but Start-1 must not do Start-2 work.
Start-3 (meaning) is strictly out of scope.

---

## 14) Implementation Notes (Non-binding but recommended)

Recommended artifacts:
- packets (append-only)
- skins (canonical forms)
- residue (non-fusable matter)
- pools (persistent clusters)
- logs (ledger trace)

Required property:
- idempotent re-runs produce identical decisions.