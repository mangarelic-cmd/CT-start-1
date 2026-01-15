start-1 (CT) — Dedup + Skin + Residue Fusion

(CLA + ε_son + stabilité + phases CT de duplication)

Start-1 est un déduplicateur de formes.
Il n’évalue ni la vérité, ni le sens, ni la valeur.
Il élimine la symétrie redondante, stabilise les formes intégrables, et conserve toute différence sous forme de résidus traçables.

Aucune interprétation.
Aucune décision sémantique.
Aucune perte d’information.

1. Rôle dans l’architecture CT

Start-1 = Symmetry / Integrity

Start-2 = Correction

Start-3 = Sens / Interprétation

Start-4 = Compression / Réponse

Start-1 ne fait qu’une chose :
👉 déduplication géométrique déterministe.

2. Entrées / Sorties
Entrées

Texte, code, équations, symboles, documents

Toute information écrite ou structurée

Sorties possibles (et uniquement celles-ci)

DUPLICATE — identité exacte déjà connue

SUTURED (Skin) — forme stable intégrable

RESIDUE — différence non fusionnée, conservée

Aucune autre sortie n’est autorisée.
2b. ?? Limitation intentionnelle : item isol?

Start-1 n?effectue aucune fusion ? partir d?un seul item.
La d?duplication par sym?trie n?cessite un groupe d?entr?es pr?sentant des formes redondantes avec variations.

Pourquoi :

La sym?trie est d?tect?e par intersection de structures communes entre plusieurs formes.

Le r?sidu fournit le contraste n?cessaire pour mesurer la compression (R_after < max(R_before)).

Avec un seul item, il n?y a ni intersection mesurable, ni r?sidu : aucune compression d?montrable.

Cons?quence :

Un item unique peut ?tre SUTURED ou RESIDUE, mais ne fusionne pas.

Ce comportement est intentionnel et garantit la v?rifiabilit? et la monotonie de Start-1.

Implication pratique :

Les tests de fusion doivent utiliser des groupes (plusieurs variantes d?une m?me forme).

Les contenus r?els (code, ?quations, phrases structur?es) arrivent naturellement en ensembles, rendant cette condition non bloquante.


3. Objets fondamentaux
Packet

Enregistrement brut, append-only

Identité déterministe (hash)

Jamais modifié après création

Skin

Forme canonique stable

Signature CT minimale

Peut absorber d’autres formes

Residue

Vecteur 5D verrouillé :
{ PI, SQRT2, SQRT3, PHI, LN5 }

Métadonnées : cycle_depth, age_band, mode dominant

Jamais détruit

Residue Pool

Ensemble vivant de clusters de résidus

Réévalué par rondes événementielles

4. Métriques CT (gelées)

CT-R
R_total = somme des composantes du résidu

CT-C
C = -R_total (cohérence monotone)

Coordonnées Son
s = r / R_total si R_total > 0, sinon uniforme

Distance Son
d_Son = ||s1 − s2||₂

Ces métriques sont non négociables.

5. Similarité et phases CT de duplication

La similarité sim ∈ [0,1] est dérivée déterministement de d_Son.

Phases CT (trace uniquement — jamais verdict)
sim	phase CT	mécanisme
< 0.61	none	pas de fusion
[0.61, 0.66)	symmetry	symétrie pure
[0.66, 0.78)	correction	symétrie corrigée
[0.78, 0.87)	expansion	symétrie étendue
[0.87, 0.946)	dissipation	symétrie dissipée
≥ 0.946	cycle	symétrie de cycle

👉 Ces phases décrivent un mécanisme causal, pas une vérité.

6. Poids de résidu (déterministe)

Le poids w ∈ [0,1] contrôle la part de différence conservée après fusion.

Points d’ancrage :

w(0.61) = 1.00

w(0.66) = 0.75

w(0.78) = 0.50

w(0.87) = 0.25

w(0.946) = 0.00

Interpolation linéaire, monotone décroissante, clamp strict [0,1].

7. Opérateur de fusion (résidu ↔ résidu)
intersection = min(a, b)
diff         = |a − b|
r_after      = intersection + w × diff


w = 0 → intersection pure (compression maximale)

w = 1 → aucune compression (fusion bloquée par le gate)

8. Conditions de merge (hard gates)

Une fusion est autorisée si et seulement si :

Même mode dominant

Même age_band

sim ≥ 0.61

(si utilisé) d_Son ≤ ε_son

Amélioration stricte :

R_after < max(R_before_A, R_before_B)


Aucun autre critère n’existe.

9. Rondes (réduction)

Rondes événementielles, jamais calendaires

Déclenchées par :

arrivée d’un nouveau résidu

création d’un cluster composite

Une ronde s’arrête au point fixe

Le nombre de passes n’est pas fixé

10. Clusters et stabilité

Les clusters portent la dynamique, pas les items isolés

Un cluster devient structurel lorsqu’il :

ne change plus sous les rondes

ou a traversé un cycle complet de phases CT

Les 118 slots (CT-1030) sont des adresses, jamais des vérités

11. Traces (audit obligatoire)

Chaque fusion trace :

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


Chaque cluster peut porter (optionnel, legacy-safe) :

last_dup_phase

last_merge_sim

last_merge_weight

12. Commandes
Build
npm run build

Ingest
npm run ingest -- \
  --file data/inbox/sample.txt \
  --uri local://sample \
  --cycle 0 \
  --eps 0.0001

Round
npm run round -- --cycle 1 --eps 0.0001 --scope event


--scope est un label de journalisation, pas une loi causale.

13. Invariants non négociables

Start-1 ne détruit rien

Start-1 ne décide rien

Start-1 n’évalue pas la vérité

Les phases CT sont des mécanismes, pas des verdicts

Toute information reste traçable

Même input + même code = mêmes résultats

Résumé

Start-1 est une centrifugeuse de formes :
la symétrie se compacte,
la différence devient résidu,
et les rondes révèlent la structure.

Références (CT)

https://zenodo.org/records/17740562

https://zenodo.org/records/17564091

https://zenodo.org/records/17802660

https://zenodo.org/records/18040237

https://zenodo.org/records/18040262

https://zenodo.org/records/18063546