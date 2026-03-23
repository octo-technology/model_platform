# Description du prétraitement des données — transaction_fraud_detector

## Source des données
Données synthétiques générées pour la démonstration (distribution calibrée sur des données réelles de fraude bancaire).
Aucune donnée personnelle réelle n'est utilisée. Tokenisation PCI-DSS v4.0 simulée.

## Schéma de données (Pandera)
- Schéma : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))
- Schéma complet disponible dans l'artefact `pandera_schema.yaml`

## Variables d'entrée
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| transaction_amount | Montant de la transaction (€) | float | in_range(0, 100 000) |
| merchant_category | Catégorie de marchand | int | in_range(0, 9) |
| transaction_hour | Heure de la transaction | int | in_range(0, 23) |
| day_of_week | Jour de la semaine | int | in_range(0, 6) |
| distance_from_home | Distance du domicile (km) | float | in_range(0, 10 000) |
| distance_from_last_txn | Distance depuis la dernière transaction (km) | float | in_range(0, 10 000) |
| ratio_to_median_amount | Ratio montant / médiane client | float | in_range(0, 1 000) |
| is_international | Transaction internationale | int | isin([0, 1]) — ⚠️ attribut sensible |
| num_transactions_24h | Transactions dans les 24h | int | in_range(1, 1 000) |
| time_since_last_txn | Temps depuis la dernière transaction (min) | float | in_range(0, 10 000) |

## Étapes de prétraitement
1. Validation du schéma Pandera (strict=True, coerce=False)
2. Split stratifié : 68% train / 12% validation / 20% test
3. Normalisation StandardScaler fitté exclusivement sur le train

## Attributs sensibles et biais potentiels
- **is_international** est un attribut sensible — corrèle avec un taux de fraude plus élevé mais peut introduire un biais géographique.
- Voir `fairness_report.json` pour les métriques ventilées par zone géographique.
