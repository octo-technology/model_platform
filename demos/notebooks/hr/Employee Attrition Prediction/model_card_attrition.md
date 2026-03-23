# Model Card — attrition_predictor

## Description
Modele de prediction de l'attrition des employes (RandomForestClassifier) qui predit la probabilite qu'un employe quitte l'entreprise dans les 6 prochains mois, a partir de donnees RH (anciennete, satisfaction, charge de travail, etc.).

Classifie **risque eleve** au sens du Reglement UE 2024/1689 (AI Act) — Annexe III §4a.

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque eleve |
| **Justification** | Systeme d'IA utilise pour prendre des decisions affectant l'acces a l'emploi et les conditions de travail des personnes physiques |
| **Reference reglementaire** | Annexe III §4a — *"Systemes d'IA utilises pour le recrutement, la selection de candidats, l'evaluation des performances, la promotion ou la resiliation de relations contractuelles de travail"* |
| **Domaine d'application (Annexe III)** | Emploi et gestion des travailleurs |
| **Article 6 — Impact significatif** | Oui — le systeme influence des decisions de gestion RH pouvant affecter directement la carriere et les conditions de travail des employes |

### Impact sur les droits fondamentaux (Article 27)
- **Droit a la non-discrimination** (Charte UE Art. 21) : le modele utilise des attributs correles a des caracteristiques protegees (age, genre). Les analyses d'equite documentees identifient des ecarts de performance par groupe.
- **Droit a la vie privee** (Charte UE Art. 7, RGPD) : le traitement de donnees personnelles (age, genre, performance) est fonde sur l'interet legitime de l'employeur, avec information prealable des employes.
- **Droit a un recours effectif** (Charte UE Art. 47) : tout employe identifie comme a risque d'attrition peut demander un entretien RH et contester l'evaluation.

## Usage prevu
### Objectif
Aide a la decision RH — identification proactive des employes a risque d'attrition pour mettre en place des actions de retention ciblees.

### Cas d'usage
1. Detection precoce des risques d'attrition sur l'ensemble du personnel
2. Priorisation des entretiens de retention par les managers RH
3. Analyse des facteurs d'attrition pour piloter la politique RH

### Utilisateurs cibles
Responsables RH, managers, directeurs des ressources humaines.

### Usages interdits
- Decisions automatiques de licenciement ou de modification de contrat sans supervision humaine
- Discrimination fondee sur l'origine ethnique, la religion ou tout autre critere protege
- Usage hors contexte RH interne de l'entreprise
- Partage des scores individuels sans accord de l'employe concerne

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : RandomForestClassifier (scikit-learn)
- **Hyperparametres** : n_estimators=200, max_depth=8, min_samples_split=10, min_samples_leaf=5, class_weight=balanced, random_state=42
- **Pretraitement** : StandardScaler (fitte sur train uniquement, pas de data leakage)
- **Validation schema** : Pandera avec contrat formel (strict=True, coerce=False)

### Signatures d'entree et sortie

**Entree** (10 features, toutes numeriques) :

| Feature | Type | Description |
|---|---|---|
| age | int | Age de l'employe (annees) — attribut protege |
| tenure_years | int | Anciennete dans l'entreprise (annees) |
| satisfaction_score | float | Score de satisfaction (0-10) |
| performance_score | float | Score de performance (0-10) |
| salary_k | float | Salaire annuel (k€) |
| num_promotions | int | Nombre de promotions recues |
| avg_weekly_hours | float | Heures travaillees par semaine en moyenne |
| num_projects | int | Nombre de projets actifs |
| distance_from_office_km | float | Distance domicile-bureau (km) |
| gender_encoded | int | Genre encode (0/1) — attribut protege |

**Sortie** :
- `predict(X)` -> int in {0, 1} — 0 = reste, 1 = attrition prevue
- `predict_proba(X)` -> float[2] — [P(reste), P(attrition)]

## Donnees d'entrainement
**Source** : Donnees synthetiques generees par simulation Monte Carlo (seed=42), calibrees sur des profils RH realistes. Aucune donnee personnelle reelle n'est utilisee.

**Volume** : 7 000 observations — train : 4 760 / validation : 840 / test : 1 400

**Donnees personnelles** : Oui — `age` et `gender_encoded` sont des attributs proteges. Base legale RGPD : interet legitime de l'employeur (Art. 6§1(f)), avec information prealable des employes.

## Evaluation des performances et equite
**Metriques globales (jeu de test)** :
- Accuracy : ~0.87
- AUC-ROC : ~0.91
- F1-score (attrition) : ~0.72
- Precision : ~0.75
- Rappel : ~0.69

**Analyse d'equite** : Performances ventilees par age et genre disponibles dans `fairness_report.json`.

## Limites connues
- Donnees synthetiques — validation externe obligatoire avant mise en production.
- Le modele ne tient pas compte des evenements externes (restructurations, crise economique).
- Risque de biais si la distribution des donnees de production s'ecarte de l'entrainement.

## Controle humain (Article 14)
- La decision finale reste humaine — le modele est un outil d'aide a la decision RH.
- Desactivation possible sans delai (kill switch plateforme).
- Chaque prediction est journalisee avec timestamp et version du modele.
- Entretien humain obligatoire avant toute action RH basee sur le score.

## Transparence (Article 13)
- Model card accessible aux RH via la plateforme Model Platform.
- L'employe est informe de l'utilisation d'un systeme d'IA pour l'evaluation du risque d'attrition.

## Explicabilite
- Feature Importance Gini disponible dans `feature_importance.csv` / `feature_importance.png`.
- SHAP TreeExplainer disponible si le package `shap` est installe.

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique, horodatage et versioning complet.
- Responsable : Octo Technology MLOps Tribe
- Chaine de responsabilite : Data Scientist -> RH Officer -> Administrateur plateforme

## Surveillance post-deploiement (Article 72)
| Indicateur | Frequence | Seuil d'alerte | Action |
|---|---|---|---|
| AUC-ROC sur donnees recentes | Hebdomadaire | < 0.85 | Reentainement planifie |
| Distribution shift (test KS) | Quotidien | p-value < 0.01 | Alerte + investigation |
| Taux de predictions attrition | Mensuel | Variation > 15% | Revue manuelle |
| Ecart de recall par genre | Mensuel | > 0.20 | Revue equite |
