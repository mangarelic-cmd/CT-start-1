# Start-1 Architecture

Start-1 is the symmetry phase of the CT pipeline.

## Pipeline
Input → Packet → Skin / Residue → Residue Pool → Rounds → Fixpoint

## Objects
- Packet: immutable raw input
- Skin: stable canonical form
- Residue: Vector5 difference
- Cluster: aggregation of residues

Start-1 est une centrifugeuse de formes : sans masse (groupe) et sans impuretés (variations), il n’y a pas de séparation mesurable.

## What Start-1 is NOT
- Not a classifier
- Not an evaluator
- Not an interpreter
- Not an AI

## Why it self-protects
Any attempt to:
- remove determinism
- add semantics
- weaken compression
will break tests immediately.

This is intentional.
