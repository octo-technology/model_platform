# Description du prétraitement des données

## Source des données
Données synthétiques générées pour la démonstration (distribution calibrée sur des données réelles de crédit).
Aucune donnée personnelle réelle n'est utilisée dans ce notebook.

## Schéma de données (Pandera)
- Schéma : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))
- Schéma complet disponible dans l'artefact `pandera_schema.yaml`
- Statistiques descriptives et rapport de validation dans `data_validation_report.json`

## Variables d'entrée
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| age | Âge de l'emprunteur | int | in_range(18, 100) — ⚠️ protégé |
| income | Revenu annuel brut (€) | int | in_range(0, 2 000 000) — ⚠️ protégé |
| loan_amount | Montant du prêt (€) | int | in_range(1, 1 000 000) |
| loan_duration_months | Durée du prêt (mois) | int | isin([12, 24, 36, 48, 60, 84]) |
| credit_score | Score de crédit | int | in_range(300, 850) |
| num_existing_loans | Crédits en cours | int | in_range(0, 50) |
| employment_years | Ancienneté emploi (années) | int | in_range(0, 60) |
| missed_payments_12m | Paiements manqués 12 mois | int | in_range(0, 12) |
| debt_to_income_ratio | Ratio dette/revenu | float | in_range(0.0, 100.0) |
| loan_to_income_ratio | Ratio prêt/revenu | float | in_range(0.0, 100.0) |

## Étapes de prétraitement
1. Validation du schéma Pandera (strict=True, coerce=False)
2. Split stratifié : 68% train / 12% validation / 20% test
3. Normalisation StandardScaler fitté exclusivement sur le train (pas de data leakage)

## Attributs protégés et biais potentiels
- **age** et **income** sont des attributs sensibles au sens du RGPD et de l'AI Act.
- Leur inclusion dans le modèle doit faire l'objet d'une validation juridique.
- Voir `fairness_report.json` pour les métriques ventilées par sous-groupes.
