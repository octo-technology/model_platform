# Fiche de conformité IA — Règlement (UE) 2024/1689 (AI Act)

> **Note d'usage** — Ce document est généré automatiquement à partir des artefacts et métadonnées MLflow enregistrés lors de l'entraînement du modèle. Les champs marqués `<!-- LLM -->` sont à compléter par inférence sur les artefacts disponibles. Les champs marqués `<!-- MLflow -->` sont extraits directement des métadonnées MLflow.

---

## 1. Identification du système d'IA

| Champ | Valeur |
|---|---|
| **Nom du système** | `<!-- MLflow: mlflow.runName ou registered model name -->` |
| **Version** | `<!-- MLflow: model version -->` |
| **Identifiant de run** | `<!-- MLflow: run_id -->` |
| **Date de création** | `<!-- MLflow: start_time -->` |
| **Équipe / responsable** | `<!-- MLflow: tag mlflow.user ou tag team -->` |
| **Environnement cible** | `<!-- MLflow: tag environment (prod / staging / dev) -->` |
| **URI du modèle (registre)** | `<!-- MLflow: model URI -->` |

---

## 2. Classification du risque (Art. 6 & Annexe III)

### 2.1 Niveau de risque

- [ ] **Risque inacceptable** — système interdit (Art. 5)
- [ ] **Risque élevé** — conformité obligatoire (Art. 6 + Annexe III)
- [ ] **Risque limité** — obligations de transparence (Art. 50)
- [ ] **Risque minimal** — aucune obligation spécifique

> **Justification** : `<!-- LLM : justifier le niveau de risque retenu au regard de l'usage prévu et des catégories listées en Annexe III (infrastructures critiques, éducation, emploi, services essentiels, répression, justice, démocratie…) -->`

### 2.2 Domaine d'application (Annexe III)

- [ ] Infrastructures critiques
- [ ] Éducation et formation professionnelle
- [ ] Emploi et gestion des travailleurs
- [ ] Accès aux services privés et publics essentiels
- [ ] Répression (law enforcement)
- [ ] Gestion des migrations et frontières
- [ ] Administration de la justice
- [ ] Processus démocratiques
- [ ] Autre : `<!-- préciser -->`

---

## 3. Description et usage prévu (Art. 9 & Annexe IV §1)

### 3.1 Objectif du système

`<!-- MLflow: tag ai_act_intended_purpose -->`

### 3.2 Cas d'usage prévus

`<!-- MLflow: tag ai_act_use_cases -->`

### 3.3 Utilisateurs cibles

`<!-- MLflow: tag ai_act_target_users -->`

### 3.4 Usages explicitement hors périmètre

`<!-- MLflow: tag ai_act_forbidden_uses -->`

---

## 4. Documentation technique (Art. 11 & Annexe IV)

### 4.1 Architecture du modèle

| Champ | Valeur |
|---|---|
| **Type de modèle** | `<!-- MLflow: tag model_type ou flavor (sklearn, pytorch, tensorflow…) -->` |
| **Flavour MLflow** | `<!-- MLflow: artifact flavors -->` |
| **Framework / librairie** | `<!-- MLflow: tag framework -->` |
| **Signature — entrées** | `<!-- MLflow: model signature inputs -->` |
| **Signature — sorties** | `<!-- MLflow: model signature outputs -->` |

### 4.2 Hyperparamètres d'entraînement

`<!-- MLflow: tous les params loggés (mlflow.log_param) -->`

| Paramètre | Valeur |
|---|---|
| `...` | `...` |

### 4.3 Données d'entraînement (Annexe IV §2d)

| Champ | Valeur |
|---|---|
| **Source des données** | `<!-- MLflow: tag data_source -->` |
| **Période couverte** | `<!-- MLflow: tag data_period -->` |
| **Volume (train / val / test)** | `<!-- MLflow: tag dataset_size ou metric dataset_* -->` |
| **Langue(s)** | `<!-- MLflow: tag data_language -->` |
| **Données personnelles impliquées** | `<!-- MLflow: tag contains_personal_data (oui/non) -->` |
| **Procédure de nettoyage / prétraitement** | `<!-- LLM : décrire sur la base des artefacts de preprocessing disponibles -->` |

### 4.4 Métriques de performance

`<!-- MLflow: toutes les métriques loggées (mlflow.log_metric) -->`

| Métrique | Valeur | Seuil d'acceptation |
|---|---|---|
| `...` | `...` | `<!-- MLflow: tag threshold_<metric> si défini -->` |

### 4.5 Évaluation de l'équité et des biais (Art. 10 §2f)

`<!-- LLM : analyser les métriques de performance ventilées par sous-groupes si disponibles dans les artefacts MLflow (ex. classification_report, fairness_report). Si absentes, signaler l'absence d'évaluation de biais. -->`

---

## 5. Limites connues et risques résiduels (Art. 9)

### 5.1 Limites techniques

`<!-- LLM : identifier les limites sur la base des métriques (ex. classes sous-performantes dans le classification_report, plages de valeurs d'entrée non couvertes) -->`

### 5.2 Distribution shift et domaine de validité

`<!-- MLflow: tag valid_input_distribution ou LLM: décrire les conditions dans lesquelles le modèle est valide -->`

### 5.3 Risques résiduels identifiés

| Risque | Probabilité | Impact | Mesure de mitigation |
|---|---|---|---|
| `...` | `...` | `...` | `...` |

---

## 6. Contrôle humain (Art. 14)

| Mesure | Statut |
|---|---|
| Intervention humaine possible avant action du système | `<!-- oui / non / partiel -->` |
| Mécanisme d'alerte en cas d'anomalie | `<!-- décrire -->` |
| Capacité de désactivation (kill switch) | `<!-- oui / non -->` |
| Journal d'audit des décisions automatisées | `<!-- décrire -->` |

---

## 7. Transparence et explicabilité (Art. 13 & 50)

| Champ | Valeur |
|---|---|
| **Explicabilité locale disponible** | `<!-- MLflow: tag explainability (SHAP, LIME…) ou artefact shap_values -->` |
| **Explicabilité globale disponible** | `<!-- MLflow: artefact feature_importance ou similar -->` |
| **Documentation accessible aux utilisateurs finaux** | `<!-- oui / non — lien -->` |
| **Information sur la nature automatisée de la décision** | `<!-- décrire comment l'utilisateur est informé -->` |

---

## 8. Robustesse, précision et cybersécurité (Art. 15)

| Champ | Valeur |
|---|---|
| **Tests de robustesse réalisés** | `<!-- MLflow: tag robustness_tests ou artefact adversarial_report -->` |
| **Résultats des tests** | `<!-- MLflow: métriques de robustesse si loggées -->` |
| **Gestion des entrées hors distribution** | `<!-- LLM : décrire sur la base des artefacts disponibles -->` |
| **Vulnérabilités connues** | `<!-- préciser -->` |

---

## 9. Traçabilité et journalisation (Art. 12)

| Champ | Valeur |
|---|---|
| **Run MLflow** | `<!-- MLflow: run_id + experiment_id -->` |
| **Hash du modèle** | `<!-- MLflow: artifact hash / version sha -->` |
| **Pipeline de CI/CD** | `<!-- MLflow: tag ci_pipeline_url -->` |
| **Dépôt de code source** | `<!-- MLflow: mlflow.source.git.repoURL -->` |
| **Commit Git** | `<!-- MLflow: mlflow.source.git.commit -->` |
| **Durée d'entraînement** | `<!-- MLflow: end_time - start_time -->` |

---

## 10. Conformité et certification (Art. 16–51)

| Obligation | Statut | Référence |
|---|---|---|
| Documentation technique complète (Annexe IV) | `<!-- conforme / partiel / non conforme -->` | Art. 11 |
| Système de gestion de la qualité | `<!-- conforme / partiel / non conforme -->` | Art. 17 |
| Enregistrement dans la base EU (si risque élevé) | `<!-- fait / à faire / N/A -->` | Art. 49 |
| Déclaration de conformité UE | `<!-- faite / à faire / N/A -->` | Art. 47 |
| Marquage CE (si risque élevé) | `<!-- fait / à faire / N/A -->` | Art. 48 |

---

## 11. Historique des révisions

| Version | Date | Auteur | Modifications |
|---|---|---|---|
| 1.0 | `<!-- date de génération -->` | `<!-- LLM / générateur automatique -->` | Création initiale à partir des artefacts MLflow |

---

*Document généré automatiquement par Model Platform — Règlement (UE) 2024/1689 relatif à l'intelligence artificielle.*
