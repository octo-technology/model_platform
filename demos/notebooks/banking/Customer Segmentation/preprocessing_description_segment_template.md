# Description du pretraitement des donnees — customer_segment_classifier

## Source des donnees
Donnees synthetiques generees pour la demonstration (distribution calibree sur des profils bancaires realistes).
Aucune donnee personnelle reelle n'est utilisee.

## Schema de donnees (Pandera)
- Schema : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))

## Variables d'entree
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| age | Age du client (annees) | int | in_range(18, 100) — attribut protege |
| income | Revenu annuel brut (EUR) | int | in_range(0, 500000) — attribut protege |
| credit_score | Score de credit | int | in_range(300, 850) |
| num_existing_loans | Nombre de credits en cours | int | in_range(0, 20) |
| avg_monthly_balance | Solde moyen mensuel (EUR) | float | in_range(-10000, 500000) |
| num_products | Nombre de produits bancaires | int | in_range(1, 15) |
| years_as_customer | Anciennete client (annees) | int | in_range(0, 50) |
| digital_engagement_score | Score d'engagement digital | float | in_range(0, 10) |

## Etapes de pretraitement
1. Validation du schema Pandera (strict=True, coerce=False)
2. KMeans clustering (k=4) pour generer les labels de segment
3. Split stratifie : 68% train / 12% validation / 20% test
4. Normalisation StandardScaler fitte sur le train uniquement

## Attributs proteges
- **age** et **income** sont des attributs sensibles — usage soumis a validation juridique.
