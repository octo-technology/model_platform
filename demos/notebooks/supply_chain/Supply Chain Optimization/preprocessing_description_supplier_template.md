# Description du pretraitement des donnees — supplier_risk_scorer

## Source des donnees
Donnees synthetiques generees pour la demonstration (distribution calibree sur des profils fournisseurs realistes).

## Schema de donnees (Pandera)
- Schema : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))

## Variables d'entree
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| on_time_delivery_rate | Taux livraison a temps | float | in_range(0, 1) |
| quality_defect_rate | Taux de defauts | float | in_range(0, 1) |
| lead_time_days | Delai livraison (jours) | int | in_range(1, 365) |
| lead_time_variability | Variabilite delai (jours) | float | in_range(0, 100) |
| financial_health_score | Score sante financiere | float | in_range(0, 10) |
| years_as_supplier | Anciennete fournisseur | int | in_range(0, 50) |
| num_incidents_12m | Incidents 12 mois | int | in_range(0, 100) |
| geographic_risk_score | Score risque geo | float | in_range(0, 10) |
| dependency_ratio | Ratio de dependance | float | in_range(0, 1) |
| certifications_score | Score certifications | float | in_range(0, 10) |

## Etapes de pretraitement
1. Validation du schema Pandera (strict=True, coerce=False)
2. Split stratifie : 68% train / 12% validation / 20% test
3. Normalisation StandardScaler fitte sur le train uniquement
