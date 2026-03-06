# Fiche de conformité IA — Règlement (UE) 2024/1689 (AI Act)

> Document généré automatiquement par Model Platform à partir des métadonnées MLflow.

---

## 1. Identification du système d'IA

| Champ | Valeur |
|---|---|
| **Nom du système** | {model_name} |
| **Version** | {version} |
| **Projet** | {project_name} |
| **Identifiant de run** | `{run_id}` |
| **Nom du run** | {run_name} |
| **Date de création** | {created_date} |
| **Équipe / responsable** | {user} |
| **URI du modèle (registre)** | `models:/{model_name}/{version}` |

---

## 2. Classification du risque (Art. 6 & Annexe III)

### 2.1 Niveau de risque

{risk_level_checkboxes}

> **Justification** : *à compléter*

### 2.2 Domaine d'application (Annexe III)

*à compléter — préciser le secteur concerné parmi les domaines de l'Annexe III*

---

## 3. Description et usage prévu (Art. 9 & Annexe IV §1)

### 3.1 Objectif du système

{description}

### 3.2 Cas d'usage prévus

*à compléter*

### 3.3 Utilisateurs cibles

*à compléter*

### 3.4 Usages explicitement hors périmètre

*à compléter — décision automatique sans supervision ; usage hors domaine prévu*

---

## 4. Documentation technique (Art. 11 & Annexe IV)

### 4.1 Architecture du modèle

| Champ | Valeur |
|---|---|
| **Type de modèle** | {model_type} |
| **Signature — entrées** | {sig_inputs} |
| **Signature — sorties** | {sig_outputs} |

### 4.2 Hyperparamètres d'entraînement

{params_table}

### 4.3 Données d'entraînement (Annexe IV §2d)

| Champ | Valeur |
|---|---|
| **Source des données** | *à compléter* |
| **Période couverte** | *à compléter* |
| **Données personnelles** | *à compléter (oui/non — préciser si données protégées au sens RGPD / AI Act Art. 10)* |
| **Prétraitement** | *à compléter* |

### 4.4 Métriques de performance

{metrics_table}

### 4.5 Évaluation de l'équité et des biais (Art. 10 §2f)

*à compléter*

---

## 5. Limites connues et risques résiduels (Art. 9)

### 5.1 Limites techniques

*à compléter*

### 5.2 Distribution shift et domaine de validité

*à compléter — préciser les plages de valeurs valides pour chaque feature*

### 5.3 Risques résiduels identifiés

| Risque | Probabilité | Impact | Mesure de mitigation |
|---|---|---|---|
| *à compléter* | *à compléter* | *à compléter* | *à compléter* |

---

## 6. Contrôle humain (Art. 14)

| Mesure | Statut |
|---|---|
| Intervention humaine possible avant action du système | *à compléter* |
| Mécanisme d'alerte en cas d'anomalie | *à compléter* |
| Capacité de désactivation (kill switch) | oui — désactivation possible par l'administrateur de la plateforme |
| Journal d'audit des décisions automatisées | oui — événements journalisés dans Model Platform |

---

## 7. Transparence et explicabilité (Art. 13 & 50)

| Champ | Valeur |
|---|---|
| **Explicabilité locale disponible** | *à compléter* |
| **Feature importance disponible** | *à compléter* |
| **Documentation accessible aux utilisateurs finaux** | *à compléter* |
| **Information sur la nature automatisée de la décision** | *à compléter* |

---

## 8. Robustesse, précision et cybersécurité (Art. 15)

| Champ | Valeur |
|---|---|
| **Tests de robustesse réalisés** | *à compléter* |
| **Résultats des tests** | *à compléter* |
| **Gestion des entrées hors distribution** | *à compléter* |
| **Vulnérabilités connues** | *à compléter* |

---

## 9. Traçabilité et journalisation (Art. 12)

| Champ | Valeur |
|---|---|
| **Run MLflow** | `{run_id}` |
| **Dépôt de code source** | *N/A* |
| **Commit Git** | *N/A* |

---

## 10. Conformité et certification (Art. 16–51)

| Obligation | Statut | Référence |
|---|---|---|
| Documentation technique complète (Annexe IV) | *à compléter* | Art. 11 |
| Système de gestion de la qualité | *à compléter* | Art. 17 |
| Enregistrement dans la base EU (si risque élevé) | *à compléter* | Art. 49 |
| Déclaration de conformité UE | *à compléter* | Art. 47 |
| Marquage CE (si risque élevé) | *à compléter* | Art. 48 |

---

## 11. Historique des révisions

| Version | Date | Auteur | Modifications |
|---|---|---|---|
| 1.0 | {now_str} | Model Platform (automatique) | Création initiale à partir des artefacts MLflow |

*Document généré automatiquement par Model Platform — Règlement (UE) 2024/1689 relatif à l'intelligence artificielle.*
