# Model Card — transaction_fraud_detector

## Description
Modèle de détection de fraude transactionnelle (RandomForestClassifier) qui évalue en temps réel le risque de fraude sur chaque paiement par carte à partir de données comportementales et contextuelles de la transaction. La décision finale de blocage reste soumise à une validation humaine ou à une procédure de contestation accessible au client.

Classifié **risque limité** au sens du Règlement UE 2024/1689 (AI Act) — Art. 50.

## Niveau de risque AI Act

| Critère | Valeur |
|---|---|
| **Classification** | Risque limité |
| **Justification** | Système de décision automatisée intervenant dans le traitement de transactions financières — obligations de transparence envers les personnes concernées (Art. 50) |
| **Référence réglementaire** | Art. 50 — *"Les déployeurs de systèmes d'IA qui prennent des décisions ou contribuent à des décisions affectant des personnes doivent informer ces personnes qu'elles font l'objet d'une décision automatisée"* |
| **Domaine d'application** | Services financiers — détection de fraude en temps réel |
| **Article 6 — Impact significatif** | Partiel — le système peut contribuer au blocage d'une transaction légitime (faux positif) |

### Impact sur les droits fondamentaux (Article 27)
- **Droit à la vie privée** (Charte UE Art. 7, RGPD) : les données traitées sont pseudonymisées (tokenisation PCI-DSS v4.0). Aucun identifiant direct n'est utilisé dans le modèle.
- **Droit à un recours effectif** (Charte UE Art. 47) : tout client dont une transaction est bloquée peut contester la décision auprès de son conseiller bancaire ou via le service client.
- **Protection des consommateurs** : conformément à l'Art. 50 AI Act, le client est informé de l'utilisation d'un système d'IA dans le traitement de sa transaction.

## Usage prévu
### Objectif
Détection en temps réel des transactions frauduleuses par carte bancaire — scoring du risque de fraude pour chaque transaction avant autorisation.

### Cas d'usage
1. Scoring en ligne des paiements e-commerce
2. Détection de fraude en point de vente physique
3. Monitoring post-autorisation pour détection retardée

### Utilisateurs cibles
Systèmes d'autorisation de paiement, équipes lutte contre la fraude, opérateurs de centres de traitement.

### Usages interdits
- Discrimination fondée sur la nationalité, l'origine géographique ou l'appartenance ethnique
- Blocage systématique de transactions sans possibilité de recours humain
- Profilage comportemental à des fins autres que la détection de fraude
- Usage hors contexte bancaire/paiement

## Documentation technique (Article 11)

### Architecture du modèle
- **Algorithme** : RandomForestClassifier (scikit-learn)
- **Hyperparamètres** : n_estimators=200, max_depth=8, min_samples_split=10, min_samples_leaf=5, class_weight=balanced, random_state=42
- **Prétraitement** : StandardScaler (fitté sur train uniquement)
- **Validation schéma** : Pandera strict=True

### Signatures d'entrée et sortie

**Entrée** (10 features) :

| Feature | Type | Description |
|---|---|---|
| transaction_amount | float | Montant de la transaction (€) |
| merchant_category | int | Catégorie de marchand (0-9) |
| transaction_hour | int | Heure (0-23) |
| day_of_week | int | Jour de la semaine (0-6) |
| distance_from_home | float | Distance du domicile (km) |
| distance_from_last_txn | float | Distance depuis la dernière transaction (km) |
| ratio_to_median_amount | float | Ratio montant / médiane client |
| is_international | int | Transaction internationale (0/1) — ⚠️ attribut sensible |
| num_transactions_24h | int | Nombre de transactions dans les 24h |
| time_since_last_txn | float | Temps depuis la dernière transaction (min) |

**Sortie** : `predict(X)` → int ∈ {0, 1} | `predict_proba(X)` → float[2]

## Données d'entraînement
**Source** : Données synthétiques (8 000 transactions) — distribution calibrée sur des profils réels de fraude bancaire. Aucune donnée personnelle réelle. Tokenisation PCI-DSS simulée.

**Volume** : 8 000 — train : 5 440 / validation : 960 / test : 1 600

**Données personnelles** : Non — données transactionnelles pseudonymisées, aucun identifiant client direct.

**Biais potentiels identifiés** : Le critère `is_international` (transaction à l'étranger) corrèle avec un taux de fraude plus élevé mais peut introduire une discrimination géographique. Son utilisation doit être validée juridiquement.

## Évaluation des performances et équité
**Métriques globales (jeu de test)** :
- Accuracy : voir notebook (variable selon seed)
- AUC-ROC : seuil d'acceptation ≥ 0.85
- Recall (fraude) : seuil d'acceptation ≥ 0.70
- F1-score (fraude) : seuil d'acceptation ≥ 0.60

**Analyse d'équité** : Performance ventilée par `is_international` — vérification de l'absence de sur-détection discriminatoire sur les transactions internationales.

### Plan d'atténuation des biais (Article 10§2)
1. **Biais géographique** : surveillance du taux de faux positifs par zone géographique — seuil max : ratio FPR international/domestique ≤ 2.0
2. **Calibration du seuil** : ajustement possible du seuil de classification selon le profil de risque opérateur
3. **Revalidation semestrielle** sur données réelles anonymisées

## Limites connues
- Données d'entraînement synthétiques — validation obligatoire sur données réelles avant production
- Sensible aux changements de comportement (nouveaux patterns de fraude non observés à l'entraînement)
- Faux positifs possibles sur les transactions atypiques légitimes (voyages, achats exceptionnels)

## Contrôle humain (Article 14)
- Toute transaction bloquée peut faire l'objet d'une révision humaine par l'équipe fraude
- Le client est informé du blocage et dispose d'un recours immédiat (appel au service client)
- Kill switch opérateur disponible pour désactivation immédiate
- Seuil de décision ajustable sans réentraînement

## Transparence et information utilisateur (Article 13)
- Conformément à l'Art. 50 AI Act, les clients sont informés de l'utilisation d'un système d'IA pour évaluer leurs transactions dans les CGU et lors d'un blocage
- Score de risque disponible pour l'équipe fraude (non divulgué au client pour des raisons de sécurité)

## Explicabilité
- **Feature Importance Gini** : disponible dans `feature_importance.csv`
- **SHAP TreeExplainer** : permet d'expliquer chaque décision individuelle à l'équipe fraude
- `is_international` mis en évidence comme attribut sensible dans les graphiques

## Robustesse (Article 15)
- Validation croisée 5-fold pour confirmer la stabilité
- Tests sur transactions aux bornes extrêmes des plages de validité
- Validation Pandera systématique avant inférence

## Traçabilité et gouvernance (Article 12)
- Run MLflow avec horodatage et run_id unique
- Versioning dans MLflow Model Registry
- Journalisation de chaque décision avec timestamp et version du modèle
- Responsable : MLOps Tribe, Octo Technology

## Système de gestion qualité (Article 17)
- Notebook reproductible avec seed fixe
- Évaluation déterministe + revue IA Act à chaque nouvelle version
- Validation Risk Officer avant déploiement en production

## Surveillance post-déploiement (Article 72)

| Indicateur | Fréquence | Seuil d'alerte | Action |
|---|---|---|---|
| AUC-ROC sur transactions récentes | Hebdomadaire | < 0.80 | Réentraînement planifié |
| Taux de faux positifs global | Quotidien | > 2% | Revue manuelle |
| Ratio FPR international/domestique | Hebdomadaire | > 2.0 | Revue équité |
| Volume de contestations clients | Mensuel | > 1% | Revue du modèle |

## Déclaration de conformité et enregistrement UE (Article 49)
- **Statut** : Risque limité — pas d'obligation d'enregistrement dans la base de données UE
- **Obligations** : transparence envers les utilisateurs (Art. 50)
- **Responsable** : Risk Officer en collaboration avec le DPO
