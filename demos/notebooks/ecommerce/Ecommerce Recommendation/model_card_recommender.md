# Model Card — product_recommender

## Description
Modele de recommandation de produits e-commerce (GradientBoostingClassifier) qui predit la probabilite qu'un client achete un produit recommande, a partir de son historique de navigation, ses achats precedents et son profil.

Classifie **risque minimal** au sens du Reglement UE 2024/1689 (AI Act) — systeme de recommandation commercial standard.

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque minimal |
| **Justification** | Systeme de recommandation commerciale — impact limite sur les droits fondamentaux, usage strictement commercial |
| **Reference reglementaire** | N/A — risque minimal |
| **Domaine d'application** | E-commerce — recommandation de produits |
| **Article 6 — Impact significatif** | Non — les recommandations influencent les achats mais ne contraignent pas les droits des consommateurs |

## Usage prevu
### Objectif
Personnalisation de l'experience d'achat en recommandant les produits les plus susceptibles d'interesser chaque client.

### Cas d'usage
1. Recommandations sur la page d'accueil et fiches produits
2. Emails de recommandation personnalises
3. Cross-sell et up-sell en parcours d'achat

### Utilisateurs cibles
Equipes e-commerce, marketing digital, product managers.

### Usages interdits
- Ciblage publicitaire base sur des caracteristiques protegees (religion, origine, sante)
- Manipulation psychologique (dark patterns)
- Discrimination tarifaire basee sur le profil utilisateur

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : GradientBoostingClassifier (scikit-learn)
- **Hyperparametres** : n_estimators=200, learning_rate=0.05, max_depth=5, subsample=0.8, random_state=42
- **Pretraitement** : StandardScaler fitte sur train uniquement
- **Validation schema** : Pandera

### Signatures d'entree et sortie

**Entree** (10 features numeriques) :

| Feature | Type | Description |
|---|---|---|
| age | int | Age du client — attribut protege |
| days_since_last_purchase | int | Jours depuis le dernier achat |
| num_purchases_30d | int | Nombre d'achats sur 30 jours |
| avg_basket_value | float | Valeur moyenne du panier (EUR) |
| num_categories_browsed | int | Nombre de categories consultees |
| session_duration_min | float | Duree moyenne de session (minutes) |
| loyalty_score | float | Score de fidelite (0-10) |
| return_rate | float | Taux de retour produits |
| product_category_encoded | int | Categorie produit recommande (0-9) |
| price_sensitivity_score | float | Score de sensibilite au prix (0-10) |

**Sortie** :
- `predict(X)` -> int in {0,1} — 0 = pas d'achat, 1 = achat probable
- `predict_proba(X)` -> float[2] — probabilites

## Donnees d'entrainement
**Source** : Donnees synthetiques (seed=42). Volume : 8 000 observations.

## Evaluation des performances
- Accuracy : ~0.82
- AUC-ROC : ~0.88
- F1-score : ~0.79

## Controle humain
- Systeme de recommandation — les clients font leurs propres choix d'achat.
- Opt-out disponible pour les clients souhaitant desactiver la personnalisation.

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique et versioning complet.
- Responsable : Octo Technology MLOps Tribe
