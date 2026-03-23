# Model Card — transaction_fraud_detector

## Description
Modèle de détection de fraude sur les transactions bancaires (RandomForestClassifier) qui évalue en temps réel la probabilité qu'une transaction soit frauduleuse, à partir de signaux comportementaux et contextuels (montant, vélocité, distance, heure, etc.).

Classifié **risque limité** au sens du Règlement UE 2024/1689 (AI Act) — Art. 50 (obligations de transparence).

## Niveau de risque AI Act
**Limité** — Hors Annexe III. Le système est un outil de détection interne qui n'appartient pas aux catégories à haut risque. Il n'évalue pas la solvabilité des personnes et n'affecte pas directement l'accès à des services essentiels.

Obligations applicables :
- Transparence envers le client si une transaction est bloquée sur la base d'une décision assistée par IA (Art. 50)
- Journalisation des prédictions avec timestamp, hash des inputs et version du modèle
- Documentation technique maintenue à jour

## Usage prévu
### Objectif
Détection automatique des transactions potentiellement frauduleuses pour déclencher un blocage préventif ou une alerte en temps réel, avant autorisation définitive.

### Cas d'usage
1. Scoring temps réel des transactions carte (paiement physique et CNP)
2. Alertes automatiques envoyées au client pour confirmation (push notification)
3. Revue a posteriori des transactions marquées comme suspectes par les équipes anti-fraude

### Utilisateurs cibles
Systèmes de core banking, équipes opérations fraude, plateformes de monitoring transactionnel.

### Usages interdits
- Blocage définitif d'un compte sans validation humaine
- Discrimination fondée sur l'origine géographique ou tout autre critère protégé
- Partage des scores de fraude avec des tiers sans base légale
- Usage comme unique motif de refus de crédit ou de fermeture de compte

## Données d'entraînement
**Source** : Données synthétiques générées pour la démonstration, distribution calibrée sur des données réelles de transactions bancaires. Aucune donnée personnelle réelle n'est utilisée.

**Volume** : 50 000 transactions — train : 34 000 / validation : 6 000 / test : 10 000

**Période** : N/A — données synthétiques

**Langue** : N/A — données tabulaires

**Données personnelles** : Non — données comportementales transactionnelles anonymisées. Aucun attribut directement identifiant n'est utilisé dans le modèle.

**Prétraitement** :
1. Validation du schéma Pandera (strict=True, coerce=False)
2. Calcul de la variable dérivée `amount_vs_avg_ratio`
3. Split stratifié : 68 % train / 12 % validation / 20 % test
4. Normalisation StandardScaler fitté exclusivement sur le train (pas de data leakage)
5. `class_weight='balanced'` pour compenser le fort déséquilibre (taux de fraude ~1–3%)

**Biais potentiels identifiés** : La distance géographique et les transactions nocturnes peuvent être corrélées avec des comportements légitimes de certains profils clients (voyageurs, travailleurs de nuit). Un écart de recall entre segments doit être surveillé.

## Évaluation des performances
**Métriques globales (jeu de test, 10 000 transactions)** : voir artefacts `classification_report.json` et `roc_curve.png`.

**Analyse par segment** : voir `segment_report.json` pour les métriques par catégorie de commerçant.

## Limites connues
- **Faux positifs** : un rappel élevé implique un taux de faux positifs non nul — des transactions légitimes peuvent être bloquées temporairement. L'expérience client doit être gérée avec des mécanismes de confirmation rapide.
- **Concept drift** : les patterns de fraude évoluent rapidement — re-entraînement mensuel recommandé.
- **Données synthétiques** : validation sur données réelles de transactions obligatoire avant mise en production.
- **Fraude organisée** : le modèle ne capture pas les réseaux de fraude coordonnés (graph-based patterns).

## Contrôle humain
- Toute décision de blocage définitif d'un compte est validée par un analyste fraude.
- Le client est notifié en cas de blocage et peut contester la décision (mécanisme de recours).
- Désactivation possible par l'administrateur de la plateforme (kill switch).
- Chaque prédiction est journalisée avec timestamp, hash des inputs et version du modèle.

## Explicabilité
- **Feature Importance Gini** (globale) : disponible dans `feature_importance.csv` / `feature_importance.png`.
- **SHAP TreeExplainer** (locale) : disponible si le package `shap` est installé (artefact `shap_summary.png`).

## Robustesse
- Validation Pandera à chaque inférence recommandée pour détecter les inputs hors domaine.
- Monitoring hebdomadaire du taux de fraude détecté vs réel pour détecter les dérives de distribution.
- Latence d'inférence cible : < 50 ms pour un usage temps réel en ligne.
