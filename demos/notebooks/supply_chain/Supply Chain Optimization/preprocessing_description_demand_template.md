# Description du pretraitement des donnees — demand_forecaster

## Source des donnees
Series temporelles synthetiques generees pour la demonstration.
Aucune donnee operationnelle reelle n'est utilisee.

## Schema de donnees (Pandera)
- Schema : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))

## Variables d'entree
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| week_of_year | Semaine de l'annee | int | in_range(1, 52) |
| month | Mois | int | in_range(1, 12) |
| is_promo | Semaine promo (0/1) | int | isin([0, 1]) |
| is_holiday_week | Semaine avec ferie (0/1) | int | isin([0, 1]) |
| lag_1_demand | Demande S-1 (unites) | float | in_range(0, 100000) |
| lag_4_demand | Demande S-4 (unites) | float | in_range(0, 100000) |
| rolling_4w_avg | Moyenne mobile 4s (unites) | float | in_range(0, 100000) |
| rolling_4w_std | Ecart-type mobile 4s | float | in_range(0, 50000) |
| price_index | Indice de prix relatif | float | in_range(0.5, 2.0) |
| competitor_promo | Promo concurrent (0/1) | int | isin([0, 1]) |

## Etapes de pretraitement
1. Validation du schema Pandera (strict=True, coerce=False)
2. Split temporel : 68% train / 12% validation / 20% test (pas de melange temporel)
3. Normalisation StandardScaler fitte sur le train uniquement

## Attributs proteges
Aucun attribut protege — outil de planification operationnelle.
