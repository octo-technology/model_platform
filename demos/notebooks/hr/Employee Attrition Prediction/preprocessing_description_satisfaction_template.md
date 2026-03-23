# Description du pretraitement des donnees — satisfaction_scorer

## Source des donnees
Donnees synthetiques generees pour la demonstration.
Aucune donnee personnelle reelle n'est utilisee dans ce notebook.

## Schema de donnees (Pandera)
- Schema : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))
- Schema complet disponible dans l'artefact `pandera_schema.yaml`

## Variables d'entree
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| tenure_years | Anciennete dans l'entreprise (annees) | int | in_range(0, 40) |
| performance_score | Score de performance (0-10) | float | in_range(0, 10) |
| salary_k | Salaire annuel (kEUR) | float | in_range(20, 200) |
| num_promotions | Nombre de promotions | int | in_range(0, 10) |
| avg_weekly_hours | Heures travaillees par semaine | float | in_range(20, 80) |
| num_projects | Nombre de projets actifs | int | in_range(1, 20) |
| distance_from_office_km | Distance domicile-bureau (km) | float | in_range(0, 200) |
| manager_rating | Note du manager (0-10) | float | in_range(0, 10) |

## Etapes de pretraitement
1. Validation du schema Pandera (strict=True, coerce=False)
2. Split stratifie par quartile de satisfaction : 68% train / 12% validation / 20% test
3. Normalisation StandardScaler fitte exclusivement sur le train (pas de data leakage)

## Attributs proteges
Aucun attribut protege — modele analytique agregat sans impact individuel direct.
