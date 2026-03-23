# Description du pretraitement des donnees — customer_churn_predictor

## Source des donnees
Donnees synthetiques generees pour la demonstration (distribution calibree sur des comportements e-commerce realistes).

## Schema de donnees (Pandera)
- Schema : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))

## Variables d'entree
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| days_since_last_purchase | Jours depuis le dernier achat | int | in_range(0, 365) |
| num_purchases_90d | Achats sur 90 jours | int | in_range(0, 200) |
| avg_basket_value | Valeur moyenne panier (EUR) | float | in_range(0, 5000) |
| total_spend_12m | Depenses 12 mois (EUR) | float | in_range(0, 100000) |
| num_returns_90d | Retours sur 90 jours | int | in_range(0, 50) |
| support_tickets_90d | Tickets support 90j | int | in_range(0, 20) |
| email_open_rate | Taux ouverture emails | float | in_range(0, 1) |
| session_frequency_30d | Sessions par semaine | float | in_range(0, 50) |
| loyalty_score | Score de fidelite (0-10) | float | in_range(0, 10) |
| nps_score | Score NPS | int | in_range(-10, 10) |

## Etapes de pretraitement
1. Validation du schema Pandera (strict=True, coerce=False)
2. Split stratifie : 68% train / 12% validation / 20% test
3. Normalisation StandardScaler fitte sur le train uniquement
