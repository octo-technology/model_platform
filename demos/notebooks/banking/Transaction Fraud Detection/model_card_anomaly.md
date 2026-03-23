# Model Card — transaction_anomaly_detector

## Description
Modèle de détection d'anomalies transactionnelles (GradientBoostingClassifier) qui identifie les comportements statistiquement inhabituels dans les flux de paiements à partir de métriques agrégées. Outil de monitoring technique interne — aucune donnée personnelle, aucun impact direct sur les clients.

Classifié **risque minimal** au sens du Règlement UE 2024/1689 (AI Act).

## Niveau de risque AI Act

| Critère | Valeur |
|---|---|
| **Classification** | Risque minimal |
| **Justification** | Système de monitoring technique interne basé sur des métriques agrégées de flux transactionnels — aucun impact direct sur les droits ou l'accès aux services des personnes |
| **Référence réglementaire** | Aucune obligation spécifique AI Act — bonne pratique documentaire |
| **Domaine d'application** | Monitoring opérationnel interne |
| **Article 6 — Impact significatif** | Non — les résultats sont utilisés pour déclencher une investigation humaine, pas pour bloquer des transactions |

### Impact sur les droits fondamentaux (Article 27)
- Aucun impact direct sur les droits des personnes — système de monitoring opérationnel interne
- Les résultats d'anomalie déclenchent uniquement une investigation par l'équipe technique

## Usage prévu
### Objectif
Détection d'anomalies statistiques dans les flux de transactions pour identifier des comportements inhabituels nécessitant une investigation technique (pannes, attaques de type card testing, problèmes d'intégration).

### Cas d'usage
1. Détection d'attaques de type "card testing" (nombreuses micro-transactions)
2. Identification de bugs d'intégration (montants aberrants)
3. Surveillance des flux nocturnes atypiques

### Utilisateurs cibles
Équipes techniques (SRE, DevOps), analystes fraude niveau 2, systèmes de monitoring automatisé.

### Usages interdits
- Blocage direct de transactions sans investigation humaine
- Profilage de clients individuels
- Décision d'accès aux services financiers

## Documentation technique (Article 11)

### Architecture du modèle
- **Algorithme** : GradientBoostingClassifier (scikit-learn)
- **Hyperparamètres** : n_estimators=150, learning_rate=0.05, max_depth=4, subsample=0.8, random_state=42
- **Prétraitement** : StandardScaler
- **Validation schéma** : Pandera strict=True

### Signatures d'entrée et sortie

**Entrée** (8 features agrégées) :

| Feature | Type | Description |
|---|---|---|
| transaction_amount | float | Montant de la transaction courante (€) |
| num_transactions_1h | int | Nombre de transactions dans la dernière heure |
| avg_amount_1h | float | Montant moyen (1h) |
| std_amount_1h | float | Écart-type des montants (1h) |
| max_amount_1h | float | Montant maximum (1h) |
| hour_of_day | int | Heure de la journée (0-23) |
| transactions_velocity | float | Vélocité des transactions |
| amount_deviation | float | Écart du montant par rapport à la moyenne (σ) |

**Sortie** : `predict(X)` → int ∈ {0, 1} | `predict_proba(X)` → float[2]

## Données d'entraînement
**Source** : Données synthétiques (6 000 observations) — métriques agrégées de flux transactionnels simulés. Aucune donnée personnelle.

**Volume** : 6 000 — train : 4 080 / validation : 720 / test : 1 200

**Données personnelles** : Non — métriques agrégées uniquement.

## Évaluation des performances et équité
**Métriques globales** : AUC-ROC seuil ≥ 0.80, Recall ≥ 0.65

**Équité** : Analyse par plage horaire — vérification de la cohérence de performance entre les différentes heures de la journée.

### Plan d'atténuation des biais
Pas d'attribut protégé — suivi de la stabilité des métriques par plage horaire et par type de marchand.

## Limites connues
- Données synthétiques — validation sur données réelles requise
- Sensible aux nouveaux patterns d'attaque non vus à l'entraînement
- Taux d'anomalie variable selon la période (nuit vs jour)

## Contrôle humain (Article 14)
- Les alertes déclenchent une investigation humaine — aucun blocage automatique
- Seuil d'alerte ajustable par l'équipe opérationnelle

## Transparence et information utilisateur (Article 13)
- Système interne — pas d'obligation de transparence envers les clients finaux
- Documentation disponible pour les équipes techniques

## Explicabilité
- Feature Importance Gini disponible
- SHAP pour analyse des cas individuels par l'équipe technique

## Robustesse (Article 15)
- Validation croisée et tests de perturbation
- Pandera schema validation avant chaque inférence

## Traçabilité et gouvernance (Article 12)
- Run MLflow avec versioning
- Responsable : MLOps Tribe, Octo Technology

## Système de gestion qualité (Article 17)
- Notebook reproductible, évaluation déterministe à chaque version

## Surveillance post-déploiement (Article 72)

| Indicateur | Fréquence | Seuil d'alerte | Action |
|---|---|---|---|
| AUC-ROC | Hebdomadaire | < 0.75 | Réentraînement |
| Taux d'anomalie détectée | Quotidien | > 15% | Investigation technique |

## Déclaration de conformité et enregistrement UE (Article 49)
- **Statut** : Risque minimal — aucune obligation réglementaire spécifique
- Documentation maintenue par bonne pratique
