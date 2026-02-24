# Model Card — credit_default_predictor

## Description
Modèle de scoring crédit bancaire (GradientBoostingClassifier) qui prédit la probabilité de défaut de paiement d'un emprunteur à partir de ses données socio-financières (âge, revenu, montant et durée du prêt, score de crédit, historique de paiements, etc.).

Classifié **risque élevé** au sens du Règlement UE 2024/1689 (AI Act) — Annexe III §5b.

## Niveau de risque AI Act
**Élevé** — Annexe III §5b : *"Systèmes d'IA destinés à évaluer la solvabilité des personnes physiques ou à établir leur score de crédit."*

Ce système intervient dans une décision susceptible d'affecter de manière significative l'accès aux services financiers. Il implique des attributs protégés (âge, revenu) et doit satisfaire aux exigences du Chapitre III Section 2 de l'AI Act (Art. 8 à 15).

## Usage prévu
### Objectif
Aide à la décision d'octroi de crédit bancaire — prédiction de la probabilité de défaut de paiement à partir de données socio-financières de l'emprunteur.

### Cas d'usage
1. Scoring crédit pour demandes de prêt personnel
2. Aide à la décision pour prêts immobiliers
3. Réévaluation du risque sur portefeuille de crédits existants

### Utilisateurs cibles
Conseillers bancaires, risk managers, systèmes de scoring automatisés supervisés par des humains.

### Usages interdits
- Décision automatique d'octroi ou de refus sans supervision humaine
- Usage hors secteur bancaire (assurances, emploi, logement, etc.)
- Discrimination fondée sur l'origine ethnique, la religion ou tout autre critère protégé
- Usage sur des mineurs de moins de 18 ans
- Contournement de la réglementation sur le crédit à la consommation

## Données d'entraînement
**Source** : Données synthétiques générées pour la démonstration, distribution calibrée sur des données réelles de crédit. Aucune donnée personnelle réelle n'est utilisée.

**Volume** : 8 000 observations — train : 5 440 / validation : 960 / test : 1 600

**Période** : N/A — données synthétiques

**Langue** : N/A — données tabulaires

**Données personnelles** : Oui — `age` et `income` sont des attributs protégés au sens du RGPD et de l'AI Act Art. 10. Leur inclusion doit être validée juridiquement.

**Prétraitement** :
1. Validation du schéma Pandera (strict=True, coerce=False) — statut : **PASS** (0 erreur)
2. Split stratifié : 68 % train / 12 % validation / 20 % test
3. Normalisation StandardScaler fitté exclusivement sur le train (pas de data leakage)
4. Variables dérivées calculées : `debt_to_income_ratio`, `loan_to_income_ratio`

**Biais potentiels identifiés** : Fort gradient du taux de défaut selon le revenu (39,2 % pour <30k€ vs 1,8 % pour >100k€). L'utilisation du revenu comme feature discriminante est un risque de biais socio-économique structurel à documenter juridiquement.

## Évaluation des performances et équité
**Métriques globales (jeu de test, 1 600 observations)** :
- Accuracy : 0.9344
- AUC-ROC : 0.9003
- F1-score (défaut) : 0.5714
- Précision (défaut) : 0.7071
- Rappel (défaut) : 0.4795

**Analyse d'équité par tranche d'âge (attribut protégé)** :

| Tranche | N | Taux défaut | Recall | AUC-ROC |
|---|---|---|---|---|
| 18-30 | 280 | 8.9% | 0.28 | 0.9034 |
| 31-45 | 528 | 9.5% | 0.54 | 0.8898 |
| 46-60 | 488 | 8.8% | 0.5349 | 0.908 |
| 60+ | 304 | 9.2% | 0.4643 | 0.9053 |

⚠️ Écart de recall notable entre les 18-30 ans et les autres tranches — le modèle détecte moins bien les défauts chez les jeunes emprunteurs.

**Analyse d'équité par tranche de revenu (attribut protégé)** :

| Tranche | N | Taux défaut | Recall | AUC-ROC |
|---|---|---|---|---|
| <30k | 174 | 40.2% | 0.7714 | 0.8978 |
| 30k-60k | 369 | 13.0% | 0.3333 | 0.8302 |
| 60k-100k | 476 | 3.4% | 0.0 | 0.8433 |
| >100k | 581 | 2.1% | 0.0 | 0.6718 |

⚠️ Recall nul pour les revenus > 60k€ malgré un AUC-ROC acceptable — asymétrie de performance inter-groupes à investiguer avant déploiement.

## Limites connues
- **Recall faible** : seulement 47.9% des vrais défauts sont détectés — risque de faux négatifs élevé.
- **Déséquilibre de classes** : taux de défaut de 9.1% — entraînement sans rééchantillonnage.
- **Domaine de validité** : age ∈ [22, 70], income ∈ [15 000, 150 000 €], credit_score ∈ [300, 850], loan_amount ∈ [1 000, 80 000 €]. Toute entrée hors de ces plages doit déclencher une alerte.
- **Données synthétiques** : validation externe sur données réelles obligatoire avant mise en production.
- **Biais structurel** : la corrélation revenu ↔ défaut intègre un biais socio-économique structurel dans le modèle.

## Contrôle humain
- La décision finale d'octroi de crédit est soumise à la validation d'un conseiller bancaire — le modèle est un outil d'aide à la décision, non une décision automatique.
- Désactivation possible par l'administrateur de la plateforme (kill switch).
- Chaque prédiction est journalisée avec timestamp, hash des inputs et version du modèle.
- Alerte si la distribution des inputs s'éloigne de plus de 2σ de la distribution d'entraînement (détection de distribution shift).
- Le demandeur est informé de l'utilisation d'un système d'IA pour l'évaluation de sa demande (Art. 50 AI Act).

## Explicabilité
- **Feature Importance Gini** (globale) : disponible dans l'artefact `feature_importance.csv` / `feature_importance.png`.
- **SHAP TreeExplainer** (locale) : disponible si le package `shap` est installé (artefact `shap_summary.png`) — statut : non installé.
- Les attributs protégés (âge, revenu) sont mis en évidence dans les graphiques d'importance.

## Robustesse
- Tests de robustesse formels non réalisés — à planifier avant mise en production.
- Domaine de validité des entrées documenté (voir section Limites connues).
- Validation Pandera à chaque inférence recommandée pour détecter les entrées hors distribution.
- Monitoring de la distribution des inputs en production prévu (alerte à 2σ).
