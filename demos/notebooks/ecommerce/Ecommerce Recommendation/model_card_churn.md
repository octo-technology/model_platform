# Model Card — customer_churn_predictor

## Description
Modele de prediction du churn client e-commerce (RandomForestClassifier) qui predit la probabilite qu'un client actif cesse d'utiliser la plateforme dans les 90 prochains jours.

Classifie **risque limite** au sens du Reglement UE 2024/1689 (AI Act) — Art. 50 : systeme de decision automatisee interagissant avec des personnes physiques (campagnes de retention ciblees).

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque limite |
| **Justification** | Systeme de decision automatisee declenchant des actions commerciales ciblees (offres de retention) aupres de personnes physiques |
| **Reference reglementaire** | Art. 50 — obligations de transparence pour les systemes interagissant avec des personnes physiques |
| **Domaine d'application** | E-commerce — retention client |
| **Article 6 — Impact significatif** | Faible — les actions declenchees sont des offres commerciales, pas des decisions contraignantes |

## Usage prevu
### Objectif
Identification proactive des clients a risque de churn pour declencher des campagnes de retention ciblees.

### Cas d'usage
1. Declenchement automatique d'offres de retention pour les clients a risque
2. Priorisation des actions de l'equipe CRM
3. Analyse des facteurs de churn pour optimiser l'experience client

### Utilisateurs cibles
Equipes CRM, marketing de retention, analystes e-commerce.

### Usages interdits
- Discrimination tarifaire basee sur le score de churn
- Manipulation psychologique des clients a risque
- Partage des scores individuels avec des tiers

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : RandomForestClassifier (scikit-learn)
- **Hyperparametres** : n_estimators=200, max_depth=8, class_weight=balanced, random_state=42
- **Pretraitement** : StandardScaler fitte sur train uniquement
- **Validation schema** : Pandera

### Signatures d'entree et sortie

**Entree** (10 features numeriques) :

| Feature | Type | Description |
|---|---|---|
| days_since_last_purchase | int | Jours depuis le dernier achat |
| num_purchases_90d | int | Achats sur 90 jours |
| avg_basket_value | float | Valeur moyenne du panier (EUR) |
| total_spend_12m | float | Depenses totales 12 mois (EUR) |
| num_returns_90d | int | Retours sur 90 jours |
| support_tickets_90d | int | Tickets support sur 90 jours |
| email_open_rate | float | Taux d'ouverture emails (0-1) |
| session_frequency_30d | float | Frequence de connexion (sessions/semaine) |
| loyalty_score | float | Score de fidelite (0-10) |
| nps_score | int | Score NPS (-10 a 10) |

**Sortie** :
- `predict(X)` -> int in {0,1} — 0 = reste, 1 = churn probable
- `predict_proba(X)` -> float[2]

## Donnees d'entrainement
**Source** : Donnees synthetiques (seed=42). Volume : 7 000 observations.

## Evaluation des performances
- Accuracy : ~0.85
- AUC-ROC : ~0.90
- F1-score (churn) : ~0.75

## Controle humain
- Les actions de retention sont validees par l'equipe CRM avant envoi massif.
- Opt-out disponible pour les clients ne souhaitant pas recevoir de communications commerciales.
- Information du client sur l'utilisation d'un systeme d'IA pour personnaliser les offres (Art. 50).

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique et versioning complet.
- Responsable : Octo Technology MLOps Tribe
