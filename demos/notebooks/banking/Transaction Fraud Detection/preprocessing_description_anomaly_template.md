# Description du prétraitement des données — transaction_anomaly_detector

## Source des données
Données synthétiques — métriques agrégées de flux transactionnels simulés.
Aucune donnée personnelle, aucun identifiant client.

## Schéma de données (Pandera)
- Schéma : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))
- Schéma complet disponible dans l'artefact `pandera_schema.yaml`

## Variables d'entrée
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| transaction_amount | Montant de la transaction courante (€) | float | in_range(0, 100 000) |
| num_transactions_1h | Transactions dans la dernière heure | int | in_range(0, 1 000) |
| avg_amount_1h | Montant moyen des transactions (1h) | float | in_range(0, 100 000) |
| std_amount_1h | Écart-type des montants (1h) | float | in_range(0, 100 000) |
| max_amount_1h | Montant maximum (1h) | float | in_range(0, 500 000) |
| hour_of_day | Heure de la journée | int | in_range(0, 23) |
| transactions_velocity | Vélocité des transactions | float | in_range(0, 10 000) |
| amount_deviation | Écart du montant par rapport à la moyenne (σ) | float | in_range(-100, 100) |

## Étapes de prétraitement
1. Validation du schéma Pandera (strict=True, coerce=False)
2. Split stratifié : 68% train / 12% validation / 20% test
3. Normalisation StandardScaler fitté exclusivement sur le train

## Attributs protégés et biais potentiels
- Aucun attribut protégé — données agrégées uniquement.
- Analyse de stabilité par plage horaire disponible dans `fairness_report.json`.
