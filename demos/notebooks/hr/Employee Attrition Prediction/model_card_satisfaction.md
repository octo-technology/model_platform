# Model Card — satisfaction_scorer

## Description
Modele de prediction du score de satisfaction des employes (Ridge Regression) qui estime le niveau de satisfaction d'un employe a partir de donnees RH objectives (charge de travail, anciennete, promotions, salaire, etc.).

Classifie **risque minimal** au sens du Reglement UE 2024/1689 (AI Act) — outil analytique interne sans impact direct sur les decisions individuelles.

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque minimal |
| **Justification** | Outil analytique interne utilise pour le pilotage agregat de la politique RH — pas de decisions individuelles automatisees |
| **Reference reglementaire** | N/A — risque minimal |
| **Domaine d'application** | Analytique RH interne |
| **Article 6 — Impact significatif** | Non — le modele produit des estimations agregees pour piloter la politique RH, pas des decisions individuelles contraignantes |

## Usage prevu
### Objectif
Estimation du niveau de satisfaction des employes pour piloter la politique RH et identifier les leviers d'amelioration des conditions de travail.

### Cas d'usage
1. Analyse des facteurs impactant la satisfaction pour orienter les decisions RH strategiques
2. Benchmarking inter-equipes pour identifier les poches de mal-etre au travail
3. Mesure de l'impact des initiatives RH (augmentations, formations, teletravail)

### Utilisateurs cibles
Direction RH, analystes RH, consultants en organisation.

### Usages interdits
- Decisions individuelles contraignantes basees uniquement sur le score predit
- Surveillance ou controle individuel des employes
- Partage des scores individuels sans anonymisation

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : Ridge Regression (scikit-learn)
- **Hyperparametres** : alpha=1.0, fit_intercept=True, random_state=42
- **Pretraitement** : StandardScaler (fitte sur train uniquement)
- **Validation schema** : Pandera avec contrat formel

### Signatures d'entree et sortie

**Entree** (8 features numeriques) :

| Feature | Type | Description |
|---|---|---|
| tenure_years | int | Anciennete dans l'entreprise (annees) |
| performance_score | float | Score de performance (0-10) |
| salary_k | float | Salaire annuel (kEUR) |
| num_promotions | int | Nombre de promotions recues |
| avg_weekly_hours | float | Heures travaillees par semaine |
| num_projects | int | Nombre de projets actifs |
| distance_from_office_km | float | Distance domicile-bureau (km) |
| manager_rating | float | Note du manager (0-10) |

**Sortie** :
- `predict(X)` -> float — score de satisfaction estime (0-10)

## Donnees d'entrainement
**Source** : Donnees synthetiques (seed=42). Volume : 5 000 observations — train : 3 400 / validation : 600 / test : 1 000.

## Evaluation des performances
- MAE : ~0.45
- RMSE : ~0.60
- R2 : ~0.82

## Limites connues
- Modele lineaire — ne capture pas les interactions non lineaires complexes.
- Donnees synthetiques — validation externe obligatoire avant usage en production.

## Controle humain
- Outil analytique interne — toutes les decisions restent humaines.
- Aucune action automatique declenchee par le score.

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique et versioning complet.
- Responsable : Octo Technology MLOps Tribe
