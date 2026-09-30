# AC82 GitHub handoff

AC82 — Bulk Evidence Vault + Sovereign Stop — is the current solver handoff.

AC81 fixed recursive re-wave loops. AC82 additionally prevents evidence-rich global packets from repeatedly serializing the same large immutable relation table during one ALL-AUX wave.

The GitHub handoff reconstructs AC82 by applying `AC82_FROM_AC78_OVERLAY_20260926.tar.xz` over the existing compact AC78 source archive.

Validated locally before publication:

- AC79 fixed-point regression
- AC81 sovereign-stop regression
- AC82 bulk-evidence-vault regression
- 12 targeted tests passed

The AC82 evidence vault preserves exact rows and adds zero truth credit.
