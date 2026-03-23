# Model Card — demand_forecaster

## Description
Modele de prevision de la demande (GradientBoostingRegressor) qui predit le volume de commandes hebdomadaires pour un produit donne, a partir de caracteristiques temporelles, historiques de ventes et indicateurs macro.

Classifie **risque minimal** au sens du Reglement UE 2024/1689 (AI Act) — outil de planification operationnelle interne sans impact direct sur des droits fondamentaux.

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque minimal |
| **Justification** | Outil de prevision operationnelle interne — pas de decisions affectant des personnes physiques |
| **Reference reglementaire** | N/A — risque minimal |
| **Domaine d'application** | Supply chain — planification des approvisionnements |
| **Article 6 — Impact significatif** | Non — les previsions guident les decisions logistiques internes |

## Usage prevu
### Objectif
Prevision de la demande hebdomadaire pour optimiser les niveaux de stock et planifier les approvisionnements.

### Cas d'usage
1. Planification des commandes fournisseurs (S&OP)
2. Optimisation des niveaux de stock et reduction des ruptures
3. Prevision des besoins en capacite logistique

### Utilisateurs cibles
Supply chain managers, planificateurs logistiques, acheteurs.

### Usages interdits
- Decisions automatiques d'approvisionnement sans validation humaine pour les commandes importantes
- Usage pour des produits a forte variabilite non representee dans les donnees d'entrainement

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : GradientBoostingRegressor (scikit-learn)
- **Hyperparametres** : n_estimators=200, learning_rate=0.05, max_depth=4, subsample=0.8, random_state=42
- **Pretraitement** : StandardScaler fitte sur train uniquement
- **Validation schema** : Pandera

### Signatures d'entree et sortie

**Entree** (10 features numeriques) :

| Feature | Type | Description |
|---|---|---|
| week_of_year | int | Semaine de l'annee (1-52) |
| month | int | Mois (1-12) |
| is_promo | int | Semaine promotionnelle (0/1) |
| is_holiday_week | int | Semaine avec jour ferie (0/1) |
| lag_1_demand | float | Demande semaine precedente (unites) |
| lag_4_demand | float | Demande il y a 4 semaines (unites) |
| rolling_4w_avg | float | Moyenne mobile 4 semaines (unites) |
| rolling_4w_std | float | Ecart-type mobile 4 semaines |
| price_index | float | Indice de prix relatif (0.5-2.0) |
| competitor_promo | int | Promotion concurrent (0/1) |

**Sortie** :
- `predict(X)` -> float — volume de commandes prevu (unites)

## Donnees d'entrainement
**Source** : Series temporelles synthetiques (seed=42). Volume : 5 000 observations.

## Evaluation des performances
- MAE : ~45 unites
- RMSE : ~65 unites
- R2 : ~0.85

## Limites connues
- Pas de gestion explicite de la saisonnalite complexe.
- Performance degradee sur des produits avec forte intermittence de la demande.
- Horizon de prevision : 1 semaine uniquement.

## Controle humain
- Les previsions sont soumises a validation humaine avant generation des bons de commande.
- Alertes automatiques si la prevision s'ecarte de +/- 30% de la moyenne historique.

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique et versioning complet.
- Responsable : Octo Technology MLOps Tribe
