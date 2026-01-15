**start-1 (CT) — Dedup + Skin + Residue Fusion**

*(CLA + ε_son + stability + CT duplication phases)*

**Start-1 is a form deduplicator.**
It does **not** evaluate truth, meaning, or value. It removes redundant symmetry, stabilizes integrable forms, and preserves every difference as traceable residues.

No interpretation. No semantic decisions. No information loss.

---

## Role in the CT architecture

**Start-1** = Symmetry / Integrity
**Start-2** = Correction
**Start-3** = Meaning / Interpretation
**Start-4** = Compression / Response

Start-1 does exactly one thing: 👉 **deterministic geometric deduplication**.

---

## Inputs / Outputs

### Inputs

Text, code, equations, symbols, documents
Any written or structured information

### Possible outputs (and only these)

* **DUPLICATE** — exact identity already known
* **SUTURED (Skin)** — stable, integrable form
* **RESIDUE** — unfused difference, preserved

No other output is allowed.

---

## Intentional limitation: isolated item

Start-1 performs **no fusion from a single item**. Symmetry-based deduplication requires a **group of inputs** presenting redundant forms with variations.

**Why:**

* Symmetry is detected via intersection of shared structures across multiple forms.
* Residue provides the contrast required to measure compression
  *(R_after < max(R_before)).*
* With a single item, there is neither measurable intersection nor residue: no demonstrable compression.

**Consequence:**

* A single item may be **SUTURED** or **RESIDUE**, but it does not merge.

This behavior is intentional and guarantees Start-1’s **verifiability and monotonicity**.

**Practical implication:**

* Fusion tests must use groups (multiple variants of the same form).
* Real content (code, equations, structured sentences) naturally arrives in sets, so this condition is non-blocking.

---

## Fundamental objects

### Packet

* Raw, append-only record
* Deterministic identity (hash)
* Never modified after creation

### Skin

* Stable canonical form
* Minimal CT signature
* Can absorb other forms

### Residue

* Locked 5D vector: **{ PI, SQRT2, SQRT3, PHI, LN5 }**
* Metadata: `cycle_depth`, `age_band`, dominant mode
* Never destroyed

### Residue Pool

* Living set of residue clusters
* Re-evaluated by event-driven rounds

---

## CT metrics (frozen)

* **CT-R**: `R_total` = sum of residue components
* **CT-C**: `C = −R_total` (monotone coherence)
* **Son coordinates**: `s = r / R_total` if `R_total > 0`, otherwise uniform
* **Son distance**: `d_Son = ||s1 − s2||₂`

These metrics are **non-negotiable**.

---

## Similarity and CT duplication phases

Similarity `sim ∈ [0,1]` is deterministically derived from `d_Son`.

**CT phases (trace only — never verdict):**

| sim range     | phase       | CT mechanism        |
| ------------- | ----------- | ------------------- |
| < 0.61        | none        | no fusion           |
| [0.61, 0.66)  | symmetry    | pure symmetry       |
| [0.66, 0.78)  | correction  | corrected symmetry  |
| [0.78, 0.87)  | expansion   | extended symmetry   |
| [0.87, 0.946) | dissipation | dissipated symmetry |
| ≥ 0.946       | cycle       | cycle symmetry      |

👉 These phases describe a **causal mechanism**, not a truth claim.

---

## Residue weight (deterministic)

Weight `w ∈ [0,1]` controls how much difference is preserved after fusion.

**Anchors:**

* `w(0.61) = 1.00`
* `w(0.66) = 0.75`
* `w(0.78) = 0.50`
* `w(0.87) = 0.25`
* `w(0.946) = 0.00`

Linear interpolation, monotone decreasing, strict clamp `[0,1]`.

---

## Fusion operator (residue ↔ residue)

```
intersection = min(a, b)
diff         = |a − b|
r_after      = intersection + w × diff
```

* `w = 0` → pure intersection (maximal compression)
* `w = 1` → no compression (merge blocked by the gate)

---

## Merge conditions (hard gates)

A merge is allowed **iff**:

* Same dominant mode
* Same `age_band`
* `sim ≥ 0.61`
* (if used) `d_Son ≤ ε_son`

**Strict improvement:**

```
R_after < max(R_before_A, R_before_B)
```

No other criterion exists.

---

## Rounds (reduction)

* Event-driven rounds, never calendar-based
* Triggered by:

  * arrival of a new residue
  * creation of a composite cluster
* A round stops at a fixed point
* Number of passes is not fixed

---

## Clusters and stability

Clusters carry the dynamics, not isolated items.

A cluster becomes **structural** when it:

* no longer changes under rounds, **or**
* has traversed a full CT phase cycle

The **118 slots (CT-1030)** are **addresses**, never truths.

---

## Traces (mandatory audit)

Each merge logs:

```
{
  "step": "merge",
  "d_son": ...,
  "sim": ...,
  "phase": "cycle | dissipation | expansion | correction | symmetry",
  "w": ...,
  "r_before_a": ...,
  "r_before_b": ...,
  "r_after": ...
}
```

Each cluster may carry (optional, legacy-safe):

* `last_dup_phase`
* `last_merge_sim`
* `last_merge_weight`

---

## Commands

**Build**

```
npm run build
```

**Ingest**

```
npm run ingest --
  --file data/inbox/sample.txt
  --uri local://sample
  --cycle 0
  --eps 0.0001
```

**Round**

```
npm run round -- --cycle 1 --eps 0.0001 --scope event
```

`--scope` is a logging label, not a causal law.

---

## Non-negotiable invariants

* Start-1 destroys nothing
* Start-1 decides nothing
* Start-1 does not evaluate truth
* CT phases are mechanisms, not verdicts
* All information remains traceable
* Same input + same code = same results

---

## Summary

**Start-1 is a centrifuge for forms:** symmetry compacts, difference becomes residue, and rounds reveal structure.

---

## References (CT)

[https://zenodo.org/records/17740562](https://zenodo.org/records/17740562)
[https://zenodo.org/records/17564091](https://zenodo.org/records/17564091)
[https://zenodo.org/records/17802660](https://zenodo.org/records/17802660)
[https://zenodo.org/records/18040237](https://zenodo.org/records/18040237)
[https://zenodo.org/records/18040262](https://zenodo.org/records/18040262)
[https://zenodo.org/records/18063546](https://zenodo.org/records/18063546)
