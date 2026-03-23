# Description du pretraitement des donnees — product_recommender

## Source des donnees
Donnees synthetiques generees pour la demonstration (distribution calibree sur des profils e-commerce realistes).
Aucune donnee client reelle n'est utilisee.

## Schema de donnees (Pandera)
- Schema : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))

## Variables d'entree
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| age | Age du client (annees) | int | in_range(18, 80) — attribut protege |
| days_since_last_purchase | Jours depuis le dernier achat | int | in_range(0, 365) |
| num_purchases_30d | Achats sur 30 jours | int | in_range(0, 100) |
| avg_basket_value | Valeur moyenne panier (EUR) | float | in_range(0, 5000) |
| num_categories_browsed | Categories consultees | int | in_range(0, 20) |
| session_duration_min | Duree session (minutes) | float | in_range(0, 300) |
| loyalty_score | Score de fidelite (0-10) | float | in_range(0, 10) |
| return_rate | Taux de retour | float | in_range(0, 1) |
| product_category_encoded | Categorie produit (0-9) | int | in_range(0, 9) |
| price_sensitivity_score | Sensibilite au prix (0-10) | float | in_range(0, 10) |

## Etapes de pretraitement
1. Validation du schema Pandera (strict=True, coerce=False)
2. Split stratifie : 68% train / 12% validation / 20% test
3. Normalisation StandardScaler fitte sur le train uniquement
