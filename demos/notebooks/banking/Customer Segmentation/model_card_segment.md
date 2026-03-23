# Model Card — customer_segment_classifier

## Description
Modele de classification des segments clients (KMeans + LogisticRegression) qui assigne chaque client a un segment de risque (Premium, Standard, Sensible, Vulnerable) a partir de ses donnees socio-financieres.

Classifie **risque minimal** au sens du Reglement UE 2024/1689 (AI Act) — outil de segmentation marketing interne sans decision contraignante.

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque minimal |
| **Justification** | Outil de segmentation interne pour personnalisation des offres — pas de decisions contraignantes sur l'acces aux services financiers |
| **Reference reglementaire** | N/A — risque minimal |
| **Domaine d'application** | Marketing bancaire — segmentation client |
| **Article 6 — Impact significatif** | Non — la segmentation influence la personnalisation des offres mais ne bloque pas l'acces aux services |

## Usage prevu
### Objectif
Segmentation de la clientele bancaire pour personnaliser les offres, adapter la communication et optimiser la relation client.

### Cas d'usage
1. Personnalisation des offres de produits bancaires par segment
2. Adaptation des campagnes marketing au profil de risque client
3. Pilotage strategique du portefeuille clients

### Utilisateurs cibles
Equipes marketing, conseillers bancaires, direction commerciale.

### Usages interdits
- Refus automatique de services base uniquement sur le segment
- Discrimination tarifaire non justifiee
- Partage des segments avec des tiers sans consentement

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : LogisticRegression avec regularisation L2 (scikit-learn)
- **Hyperparametres** : C=1.0, max_iter=500, random_state=42, class_weight=balanced
- **Pretraitement** : StandardScaler + encodage segment KMeans (4 clusters)
- **Validation schema** : Pandera avec contrat formel

### Signatures d'entree et sortie

**Entree** (8 features numeriques) :

| Feature | Type | Description |
|---|---|---|
| age | int | Age du client (annees) — attribut protege |
| income | int | Revenu annuel brut (EUR) — attribut protege |
| credit_score | int | Score de credit interne |
| num_existing_loans | int | Nombre de credits en cours |
| avg_monthly_balance | float | Solde moyen mensuel (EUR) |
| num_products | int | Nombre de produits bancaires detenus |
| years_as_customer | int | Anciennete client (annees) |
| digital_engagement_score | float | Score d'engagement digital (0-10) |

**Sortie** :
- `predict(X)` -> int in {0,1,2,3} — segment client (0=Vulnerable, 1=Sensible, 2=Standard, 3=Premium)
- `predict_proba(X)` -> float[4] — probabilites par segment

## Donnees d'entrainement
**Source** : Donnees synthetiques (seed=42). Volume : 6 000 observations — train : 4 080 / validation : 720 / test : 1 200.

## Evaluation des performances
- Accuracy : ~0.78
- F1-score macro : ~0.76
- AUC-ROC (OvR) : ~0.88

## Controle humain
- La segmentation est un outil analytique — les decisions commerciales restent humaines.
- Revision trimestrielle des segments par l'equipe marketing.

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique et versioning complet.
- Responsable : Octo Technology MLOps Tribe
