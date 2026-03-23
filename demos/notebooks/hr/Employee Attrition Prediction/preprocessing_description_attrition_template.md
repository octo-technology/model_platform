# Description du pretraitement des donnees — attrition_predictor

## Source des donnees
Donnees synthetiques generees pour la demonstration (distribution calibree sur des profils RH realistes).
Aucune donnee personnelle reelle n'est utilisee dans ce notebook.

## Schema de donnees (Pandera)
- Schema : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))
- Schema complet disponible dans l'artefact `pandera_schema.yaml`
- Statistiques descriptives et rapport de validation dans `data_validation_report.json`

## Variables d'entree
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| age | Age de l'employe (annees) | int | in_range(18, 65) — attribut protege |
| tenure_years | Anciennete dans l'entreprise (annees) | int | in_range(0, 40) |
| satisfaction_score | Score de satisfaction (0-10) | float | in_range(0, 10) |
| performance_score | Score de performance (0-10) | float | in_range(0, 10) |
| salary_k | Salaire annuel (kEUR) | float | in_range(20, 200) |
| num_promotions | Nombre de promotions | int | in_range(0, 10) |
| avg_weekly_hours | Heures travaillees par semaine | float | in_range(20, 80) |
| num_projects | Nombre de projets actifs | int | in_range(1, 20) |
| distance_from_office_km | Distance domicile-bureau (km) | float | in_range(0, 200) |
| gender_encoded | Genre encode (0/1) | int | isin([0, 1]) — attribut protege |

## Etapes de pretraitement
1. Validation du schema Pandera (strict=True, coerce=False)
2. Split stratifie : 68% train / 12% validation / 20% test
3. Normalisation StandardScaler fitte exclusivement sur le train (pas de data leakage)

## Attributs proteges et biais potentiels
- **age** et **gender_encoded** sont des attributs sensibles au sens du RGPD et de l'AI Act.
- Leur inclusion dans le modele doit faire l'objet d'une validation juridique RH.
- Voir `fairness_report.json` pour les metriques ventilees par sous-groupes.
