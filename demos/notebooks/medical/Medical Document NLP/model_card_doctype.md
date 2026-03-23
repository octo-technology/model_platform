# Model Card — document_type_classifier

## Description
Modele de classification du type de documents medicaux (TF-IDF + LinearSVC) qui categorise automatiquement les comptes-rendus medicaux synthetiques en types (compte-rendu de consultation, ordonnance, compte-rendu d'hospitalisation, resultat d'examen, lettre de sortie).

Classifie **risque minimal** au sens du Reglement UE 2024/1689 (AI Act) — outil de tri et d'organisation documentaire sans impact sur les decisions medicales.

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque minimal |
| **Justification** | Outil de tri documentaire interne — n'influence pas les decisions medicales, sert uniquement a l'organisation du systeme d'information |
| **Reference reglementaire** | N/A — risque minimal |
| **Domaine d'application** | Gestion documentaire medicale |
| **Article 6 — Impact significatif** | Non — une erreur de classification entraine un mauvais rangement du document, sans impact direct sur les soins |

## Usage prevu
### Objectif
Classification automatique des documents medicaux pour leur archivage et leur indexation dans le systeme d'information hospitalier.

### Cas d'usage
1. Tri automatique des documents entrants dans le DPI (Dossier Patient Informatise)
2. Indexation pour la recherche documentaire
3. Controle qualite de la completude du dossier patient

### Utilisateurs cibles
Secretaires medicales, informaticiens hospitaliers, archivistes medicaux.

### Usages interdits
- Decisions medicales basees sur la classification du document
- Suppression automatique de documents mal classes

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : TF-IDF (max_features=3000, ngram_range=(1,2)) + LinearSVC (C=1.0, max_iter=2000)
- **Pretraitement** : TF-IDF vectorizer fitte sur train uniquement
- **Validation schema** : Pandera

### Signatures d'entree et sortie

**Entree** : texte libre (document medical synthetique)

**Sortie** :
- `predict(X)` -> int in {0,1,2,3,4} — type de document
  - 0 = Compte-rendu de consultation
  - 1 = Ordonnance
  - 2 = Compte-rendu d'hospitalisation
  - 3 = Resultat d'examen
  - 4 = Lettre de sortie

## Donnees d'entrainement
**Source** : Textes medicaux synthetiques (seed=42). Volume : 3 000 observations — train : 2 040 / validation : 360 / test : 600.

## Evaluation des performances
- Accuracy : ~0.91
- F1-score macro : ~0.90

## Controle humain
- Outil de tri documentaire — verification humaine possible avant archivage definitif.
- Aucune action irreversible sans validation.

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique et versioning complet.
- Responsable : Octo Technology MLOps Tribe
