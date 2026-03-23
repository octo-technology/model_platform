# Model Card — supplier_risk_scorer

## Description
Modele de scoring du risque fournisseur (LogisticRegression) qui evalue la probabilite qu'un fournisseur connaisse une defaillance d'approvisionnement dans les 3 prochains mois, a partir de donnees de performance historique et d'indicateurs de solidite financiere.

Classifie **risque limite** au sens du Reglement UE 2024/1689 (AI Act) — Art. 50 : systeme de decision automatisee pouvant affecter les relations contractuelles avec des entreprises tierces.

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque limite |
| **Justification** | Systeme de scoring automatise affectant les decisions contractuelles avec des fournisseurs (personnes morales) — obligations de transparence Art. 50 |
| **Reference reglementaire** | Art. 50 — obligations de transparence pour les systemes de decision automatisee |
| **Domaine d'application** | Supply chain — gestion du risque fournisseur |
| **Article 6 — Impact significatif** | Modere — le score peut influencer des decisions contractuelles (reduction des commandes, qualification fournisseur) |

## Usage prevu
### Objectif
Evaluation proactive du risque de defaillance fournisseur pour securiser la supply chain et prioriser les actions de mitigation.

### Cas d'usage
1. Scoring periodique du portefeuille fournisseurs pour identifier les risques
2. Aide a la decision pour les renouvellements de contrats fournisseurs
3. Declenchement de plans de contingence (second source, stock de securite)

### Utilisateurs cibles
Acheteurs, risk managers supply chain, directeurs achats.

### Usages interdits
- Resiliation automatique de contrats sans validation humaine
- Discrimination basee sur l'origine geographique du fournisseur non justifiee par des risques objectifs
- Usage sur des donnees financieres confidentielles sans accord

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : LogisticRegression (scikit-learn) avec regularisation L2
- **Hyperparametres** : C=1.0, max_iter=500, class_weight=balanced, random_state=42
- **Pretraitement** : StandardScaler fitte sur train uniquement
- **Validation schema** : Pandera

### Signatures d'entree et sortie

**Entree** (10 features numeriques) :

| Feature | Type | Description |
|---|---|---|
| on_time_delivery_rate | float | Taux de livraison a temps (0-1) |
| quality_defect_rate | float | Taux de defauts qualite (0-1) |
| lead_time_days | int | Delai moyen de livraison (jours) |
| lead_time_variability | float | Variabilite du delai (jours) |
| financial_health_score | float | Score de sante financiere (0-10) |
| years_as_supplier | int | Anciennete fournisseur (annees) |
| num_incidents_12m | int | Incidents sur 12 mois |
| geographic_risk_score | float | Score de risque geographique (0-10) |
| dependency_ratio | float | Ratio de dependance (% achats) |
| certifications_score | float | Score de certifications qualite (0-10) |

**Sortie** :
- `predict(X)` -> int in {0,1} — 0 = risque faible, 1 = risque de defaillance eleve
- `predict_proba(X)` -> float[2]

## Donnees d'entrainement
**Source** : Donnees synthetiques (seed=42). Volume : 4 000 observations.

## Evaluation des performances
- Accuracy : ~0.84
- AUC-ROC : ~0.89
- F1-score (risque eleve) : ~0.78

## Controle humain
- Les scores sont presentes aux acheteurs pour decision humaine — pas d'action automatique.
- Les fournisseurs identifies a risque eleve sont informes de l'evaluation et peuvent fournir des elements complementaires.
- Information des fournisseurs sur l'utilisation d'un systeme d'IA (Art. 50).

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique et versioning complet.
- Responsable : Octo Technology MLOps Tribe
