# Description du prétraitement des données

## Source des données
Données synthétiques générées pour la démonstration (distribution calibrée sur des données réelles de transactions bancaires).
Aucune donnée personnelle réelle n'est utilisée dans ce notebook.

## Schéma de données (Pandera)
- Schéma : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))
- Schéma complet disponible dans l'artefact `pandera_schema.yaml`
- Rapport de validation dans `data_validation_report.json`

## Variables d'entrée
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| transaction_amount | Montant de la transaction (€) | float | in_range(0.01, 100 000.0) |
| merchant_category | Catégorie commerçant (0=alimentation … 5=autre) | int | isin([0, 1, 2, 3, 4, 5]) |
| hour_of_day | Heure de la transaction (0–23) | int | in_range(0, 23) |
| is_weekend | Week-end (1=oui, 0=non) | int | isin([0, 1]) |
| distance_from_home_km | Distance domicile → transaction (km) | float | in_range(0.0, 20 000.0) |
| nb_transactions_24h | Nb transactions client sur 24 h | int | in_range(1, 200) |
| amount_vs_avg_ratio | Ratio montant / moyenne mensuelle (variable dérivée) | float | in_range(0.0, 500.0) |
| is_international | Transaction internationale (1=oui, 0=non) | int | isin([0, 1]) |
| time_since_last_txn_min | Délai depuis dernière transaction (minutes) | float | in_range(0.0, 10 000.0) |
| card_present | Carte physique présente (0=CNP, 1=physique) | int | isin([0, 1]) |

## Étapes de prétraitement
1. Validation du schéma Pandera (strict=True, coerce=False)
2. Calcul de la variable dérivée `amount_vs_avg_ratio`
3. Split stratifié : 68 % train / 12 % validation / 20 % test
4. Normalisation StandardScaler fitté exclusivement sur le train (pas de data leakage)
5. `class_weight='balanced'` pour compenser le déséquilibre de classes

## Attributs sensibles
Aucun attribut personnel ou directement identifiant — données comportementales anonymisées.
Aucune analyse d'équité sur attribut protégé requise pour ce niveau de risque.
