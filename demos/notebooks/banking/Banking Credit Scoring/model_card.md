# Model Card — credit_default_predictor

## Description
Modèle de scoring crédit bancaire (GradientBoostingClassifier) qui prédit la probabilité de défaut de paiement d'un emprunteur à partir de ses données socio-financières (âge, revenu, montant et durée du prêt, score de crédit, historique de paiements, etc.).

Classifié **risque élevé** au sens du Règlement UE 2024/1689 (AI Act) — Annexe III §5b.

## Niveau de risque AI Act

| Critère | Valeur |
|---|---|
| **Classification** | Risque élevé |
| **Justification** | Système d'IA destiné à évaluer la solvabilité de personnes physiques — décision susceptible d'affecter de manière significative l'accès aux services financiers, impliquant des attributs protégés (âge, revenu) |
| **Référence réglementaire** | Annexe III §5b — *"Systèmes d'IA destinés à évaluer la solvabilité des personnes physiques ou à établir leur score de crédit, à l'exception des systèmes d'IA mis en service par des micro et petites entreprises pour leur propre usage"* |
| **Domaine d'application (Annexe III)** | Services financiers — évaluation de solvabilité et scoring de crédit |
| **Article 6 — Impact significatif** | Oui — le système intervient dans une décision d'octroi de crédit pouvant affecter l'accès aux services financiers, un droit fondamental lié à la dignité et à l'inclusion économique des personnes |

### Impact sur les droits fondamentaux (Article 27)
- **Droit à la non-discrimination** (Charte UE Art. 21) : le modèle utilise des attributs corrélés à des caractéristiques protégées (âge, revenu). Les analyses d'équité documentées montrent des écarts de performance par groupe qu'il convient de surveiller et corriger.
- **Droit à la vie privée** (Charte UE Art. 7, RGPD) : le traitement de données personnelles (âge, revenu) est fondé sur l'intérêt légitime de l'établissement de crédit pour l'évaluation du risque, conformément à l'Art. 6§1(f) RGPD.
- **Droit à un recours effectif** (Charte UE Art. 47) : toute personne dont la demande de crédit est refusée sur la base du score peut contester la décision auprès du conseiller bancaire et demander une révision humaine complète (voir section Contrôle humain).
- **Protection des consommateurs** : le système est utilisé comme aide à la décision uniquement ; la décision finale reste humaine, conformément à l'Art. 22 RGPD (droit de ne pas faire l'objet d'une décision entièrement automatisée).

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

## Documentation technique (Article 11)

### Architecture du modèle
- **Algorithme** : GradientBoostingClassifier (scikit-learn)
- **Hyperparamètres** : n_estimators=200, learning_rate=0.05, max_depth=4, min_samples_split=20, min_samples_leaf=10, subsample=0.8, max_features=sqrt, random_state=42
- **Prétraitement** : StandardScaler (fitté sur train uniquement, pas de data leakage)
- **Validation schéma** : Pandera avec contrat formel (strict=True, coerce=False)

### Signatures d'entrée et sortie

**Entrée** (10 features, toutes numériques) :

| Feature | Type | Plage valide | Description |
|---|---|---|---|
| age | int | [22, 70] | Âge de l'emprunteur (années) — attribut protégé |
| income | int | [15 000, 150 000] | Revenu annuel brut (€) — attribut protégé |
| loan_amount | int | [1 000, 80 000] | Montant du prêt demandé (€) |
| loan_duration_months | int | {12, 24, 36, 48, 60, 84} | Durée du prêt (mois) |
| credit_score | int | [300, 850] | Score de crédit interne |
| num_existing_loans | int | [0, 5] | Nombre de crédits en cours |
| employment_years | int | [0, 34] | Ancienneté dans l'emploi actuel (années) |
| missed_payments_12m | int | [0, 4] | Paiements manqués sur les 12 derniers mois |
| debt_to_income_ratio | float | [0.0, 5.0] | Ratio dette/revenu (variable dérivée) |
| loan_to_income_ratio | float | [0.0, 5.0] | Ratio prêt/revenu (variable dérivée) |

**Sortie** :
- `predict(X)` → int ∈ {0, 1} — 0 = pas de défaut, 1 = défaut prédit
- `predict_proba(X)` → float[2] — [P(non défaut), P(défaut)] — probabilités calibrées

La signature MLflow est enregistrée automatiquement via `infer_signature()` et un `input_example` de 3 lignes est loggé avec le modèle.

## Données d'entraînement
**Source** : Données synthétiques générées par simulation Monte Carlo avec seed fixe (numpy random_state=42). La distribution est calibrée sur des profils réalistes de crédit bancaire français. La probabilité de défaut est modélisée par une fonction logistique combinant l'ensemble des features avec des coefficients réalistes. Aucune donnée personnelle réelle n'est utilisée.

**Volume** : 8 000 observations — train : 5 440 / validation : 960 / test : 1 600

**Période** : N/A — données synthétiques générées à la date d'entraînement

**Langue** : N/A — données tabulaires numériques

**Données personnelles** : Oui — `age` et `income` sont des attributs protégés au sens du RGPD (Art. 9) et de l'AI Act (Art. 10). Leur inclusion est justifiée par la nécessité d'évaluer la capacité de remboursement de l'emprunteur (intérêt légitime, Art. 6§1(f) RGPD). La base légale RGPD est documentée et validée par le DPO de l'établissement.

**Prétraitement** :
1. Validation du schéma Pandera (strict=True, coerce=False) — statut : **PASS** (0 erreur)
2. Split stratifié : 68 % train / 12 % validation / 20 % test (stratification sur la variable cible `default`)
3. Normalisation StandardScaler fitté exclusivement sur le train (pas de data leakage)
4. Variables dérivées calculées : `debt_to_income_ratio` = loan_amount / income, `loan_to_income_ratio` = loan_amount / income (clippées à [0, 5])

**Biais potentiels identifiés** : Fort gradient du taux de défaut selon le revenu (39,2 % pour <30k€ vs 1,8 % pour >100k€). L'utilisation du revenu comme feature discriminante est un risque de biais socio-économique structurel.

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

### Plan d'atténuation des biais (Article 10§2)
Les biais identifiés font l'objet du plan d'action suivant :

1. **Recall nul sur revenus élevés** — Le faible taux de défaut dans ces tranches (<3,5%) rend la détection difficile. Actions : (a) rééchantillonnage SMOTE ciblé sur les tranches sous-représentées en défauts, (b) ajustement du seuil de classification par tranche de revenu (seuils adaptatifs), (c) seuil d'acceptabilité fixé : recall ≥ 0.10 pour toute tranche avec N ≥ 50.
2. **Écart de recall par âge (18-30 ans)** — Les jeunes emprunteurs ont un recall de 0.28 vs 0.54 pour les 31-45 ans. Actions : (a) enrichissement des features d'historique pour les primo-emprunteurs, (b) calibration du seuil par tranche d'âge, (c) seuil d'acceptabilité fixé : écart max de recall inter-groupes ≤ 0.20.
3. **Métriques d'équité formelles** — Tests de parité démographique (Demographic Parity Ratio ≥ 0.80) et d'égalité des chances (Equalized Odds Difference ≤ 0.10) à calculer et monitorer en continu.
4. **Validation externe** — Avant mise en production, le modèle sera validé sur un échantillon de données réelles anonymisées pour confirmer que les biais identifiés sur données synthétiques sont représentatifs.

## Limites connues
- **Recall faible** : seulement 47.9% des vrais défauts sont détectés — risque de faux négatifs élevé.
- **Déséquilibre de classes** : taux de défaut de 9.1% — entraînement sans rééchantillonnage.
- **Domaine de validité** : age ∈ [22, 70], income ∈ [15 000, 150 000 €], credit_score ∈ [300, 850], loan_amount ∈ [1 000, 80 000 €]. Toute entrée hors de ces plages doit déclencher une alerte.
- **Données synthétiques** : validation externe sur données réelles obligatoire avant mise en production.
- **Biais structurel** : la corrélation revenu ↔ défaut intègre un biais socio-économique structurel dans le modèle.

## Contrôle humain (Article 14)
- La décision finale d'octroi de crédit est soumise à la validation d'un conseiller bancaire — le modèle est un outil d'aide à la décision, non une décision automatique (conformité Art. 22 RGPD).
- Désactivation possible par l'administrateur de la plateforme (kill switch) sans délai.
- Chaque prédiction est journalisée avec timestamp, hash des inputs et version du modèle.
- Alerte si la distribution des inputs s'éloigne de plus de 2σ de la distribution d'entraînement (détection de distribution shift).
- Le demandeur est informé de l'utilisation d'un système d'IA pour l'évaluation de sa demande (Art. 50 AI Act).
- **Procédure de contestation** : tout demandeur dont la demande est refusée peut demander une révision humaine complète de son dossier auprès de son conseiller bancaire. Le conseiller a accès au score du modèle, aux features d'importance (SHAP local), et peut outrepasser la recommandation du modèle. La contestation est enregistrée et traçable.
- **Formation des opérateurs** : les conseillers bancaires reçoivent une formation de 2h couvrant : (a) fonctionnement du modèle et interprétation du score, (b) limites connues et biais identifiés, (c) procédure de contestation et d'escalade, (d) situations où le modèle ne doit pas être utilisé.

## Transparence et information utilisateur (Article 13)
- **Guide d'interprétation des scores** : score < 0.3 = risque faible, 0.3–0.6 = risque modéré (analyse approfondie recommandée), > 0.6 = risque élevé (justification renforcée requise pour octroi). Ces seuils sont indicatifs et ne se substituent pas au jugement du conseiller.
- **Documentation accessible** : la model card est mise à disposition des risk managers et conseillers via la plateforme Model Platform. Un résumé simplifié est intégré au guide utilisateur du logiciel de scoring.
- **Information du demandeur** : conformément à l'Art. 50 AI Act, le demandeur est informé que sa demande fait l'objet d'une évaluation par un système d'IA, et qu'il dispose d'un droit de contestation avec révision humaine.

## Explicabilité
- **Feature Importance Gini** (globale) : disponible dans l'artefact `feature_importance.csv` / `feature_importance.png`.
- **SHAP TreeExplainer** (locale) : disponible si le package `shap` est installé (artefact `shap_summary.png`). Permet d'expliquer chaque prédiction individuelle — quelles features ont contribué positivement ou négativement au score.
- Les attributs protégés (âge, revenu) sont mis en évidence dans les graphiques d'importance.
- Les explications SHAP locales sont accessibles au conseiller bancaire via l'interface de scoring pour chaque demande traitée.

## Robustesse (Article 15)
### Tests réalisés
1. **Validation croisée stratifiée** (5-fold) : AUC-ROC moyen = 0.898 ± 0.012 — stabilité confirmée.
2. **Test de perturbation des entrées** : bruit gaussien (σ = 0.05) ajouté sur les features normalisées — dégradation AUC-ROC ≤ 2% → modèle stable face aux perturbations mineures.
3. **Test hors domaine** : entrées aux bornes extrêmes du domaine de validité — prédictions cohérentes, pas de comportement aberrant.
4. **Validation Pandera systématique** : le schéma de données est validé avant chaque inférence pour rejeter les entrées hors spécification.

### Mesures de cybersécurité
- Le modèle est servi via une API REST avec authentification JWT et HTTPS.
- Les entrées sont validées par le schéma Pandera avant traitement (protection contre les injections de données malveillantes).
- Le modèle sérialisé est stocké dans MLflow avec traçabilité complète (run_id, hash des artefacts).
- Accès au modèle restreint aux utilisateurs authentifiés de la plateforme avec contrôle d'accès par rôle (RBAC).

## Traçabilité et gouvernance (Article 12)
- **Run MLflow** : identifiant unique du run d'entraînement avec horodatage précis
- **Versioning** : chaque entraînement produit une nouvelle version du modèle enregistré dans MLflow Model Registry
- **Responsable** : philippe.stepniewski (MLOps Tribe, Octo Technology)
- **Dépôt de code source** : le code d'entraînement est versionné dans le dépôt Git `model_platform` avec historique complet des commits
- **Journalisation** : tous les événements (déploiement, prédictions, désactivation) sont journalisés dans la plateforme Model Platform avec timestamp et identifiant utilisateur
- **Chaîne de responsabilité** : Data Scientist (développement et validation) → Risk Officer (validation conformité) → Administrateur plateforme (déploiement et supervision)
- **Procédure de modification** : toute modification du modèle nécessite (a) une nouvelle version MLflow, (b) une réévaluation de conformité déterministe et LLM, (c) une validation par le Risk Officer avant déploiement en production

## Système de gestion qualité (Article 17)
Le modèle s'inscrit dans le système de gestion qualité de l'organisation :
- **Processus de développement** : notebook reproductible avec seed fixe, validation Pandera, analyse d'équité systématique
- **Processus de validation** : évaluation déterministe automatisée (critères obligatoires et recommandés) + revue IA Act par LLM
- **Processus de déploiement** : déploiement via la plateforme Model Platform avec contrôle d'accès, versioning, et kill switch
- **Gestion des non-conformités** : les écarts identifiés lors des revues de conformité sont tracés dans le plan d'actions et assignés à un responsable avec échéance
- **Documentation** : model card maintenue à jour à chaque version du modèle, artefacts de validation archivés dans MLflow

## Surveillance post-déploiement (Article 72)

### Plan de surveillance continue
| Indicateur | Fréquence | Seuil d'alerte | Responsable | Action |
|---|---|---|---|---|
| AUC-ROC sur données récentes | Hebdomadaire | < 0.85 | ML Engineer | Réentraînement planifié |
| Distribution shift (test KS) | Quotidien | p-value < 0.01 | ML Engineer | Alerte + investigation |
| Taux de prédictions positives | Quotidien | Variation > 20% | Risk Officer | Revue manuelle |
| Recall par tranche d'âge | Mensuel | Écart inter-groupes > 0.25 | Risk Officer | Revue équité |
| Recall par tranche de revenu | Mensuel | Recall = 0 sur une tranche | Risk Officer | Ajustement seuils |
| Volume de contestations | Mensuel | > 5% des refus | Product Owner | Revue du modèle |

### Procédures opérationnelles
- **Réentraînement** : déclenché si AUC-ROC < 0.85 ou distribution shift détecté. Le processus suit le même pipeline notebook avec les données actualisées. Chaque réentraînement produit une nouvelle version MLflow et déclenche une réévaluation de conformité.
- **Retrait d'urgence** : l'administrateur plateforme peut désactiver le modèle immédiatement via le kill switch. Un modèle de fallback (règles métier simples) prend le relais.
- **Reporting** : rapport mensuel de performance et conformité transmis au Risk Officer et au DPO. Les incidents (dégradation performance, biais détecté, contestation) sont documentés et tracés.

## Déclaration de conformité et enregistrement UE (Article 49)
- **Statut** : en cours de préparation — le dossier de conformité sera constitué avant mise en production
- **Éléments prévus** : déclaration de conformité UE (Art. 47), enregistrement dans la base de données de l'UE (Art. 49), marquage CE
- **Responsable** : Risk Officer en collaboration avec le service juridique
