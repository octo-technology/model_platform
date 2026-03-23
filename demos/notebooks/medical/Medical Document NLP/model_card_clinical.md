# Model Card — clinical_entity_extractor

## Description
Modele de classification de textes medicaux (TF-IDF + LogisticRegression) qui identifie la presence d'entites cliniques pertinentes (mentions de pathologies, symptomes, traitements) dans des comptes-rendus medicaux synthetiques.

Classifie **risque eleve** au sens du Reglement UE 2024/1689 (AI Act) — Annexe III §5a : systeme d'IA utilise dans le domaine de la sante pour aider au diagnostic ou au traitement medical.

## Niveau de risque AI Act

| Critere | Valeur |
|---|---|
| **Classification** | Risque eleve |
| **Justification** | Systeme d'IA destine a soutenir des decisions medicales — classe comme systeme a risque eleve car son utilisation incorrecte pourrait affecter la sante des patients |
| **Reference reglementaire** | Annexe III §5a — *"Systemes d'IA utilises comme dispositifs medicaux au sens du droit de l'Union ou utilises pour soutenir des professionnels de sante dans la prise de decisions de diagnostic ou therapeutiques"* |
| **Domaine d'application (Annexe III)** | Sante — aide au diagnostic et a l'analyse de documents medicaux |
| **Article 6 — Impact significatif** | Oui — une extraction incorrecte d'entites cliniques peut induire en erreur un professionnel de sante et impacter les soins prodigues |

### Impact sur les droits fondamentaux (Article 27)
- **Droit a la sante** (Charte UE Art. 35) : le modele est utilise comme aide a la lecture de documents medicaux — une erreur d'extraction peut conduire a des informations manquantes ou incorrectes transmises au medecin.
- **Droit a la vie privee** (Charte UE Art. 7, RGPD) : les textes medicaux contiennent des donnees de sante (categorie speciale Art. 9 RGPD). Base legale : soins de sante (Art. 9§2(h) RGPD).
- **Droit a un recours effectif** (Charte UE Art. 47) : le professionnel de sante doit pouvoir verifier et corriger toute extraction incorrecte avant d'agir sur les informations extraites.

## Usage prevu
### Objectif
Extraction automatique d'entites cliniques (pathologies, symptomes, traitements) depuis des comptes-rendus medicaux pour alimenter des systemes d'information hospitaliers.

### Cas d'usage
1. Pre-annotation de comptes-rendus medicaux pour validation par un professionnel de sante
2. Structuration automatique de donnees medicales non structurees
3. Aide a la recherche clinique — extraction de cohortes a partir de textes

### Utilisateurs cibles
Medecins, infirmiers, informaticiens medicaux, equipes de recherche clinique.

### Usages interdits
- Diagnostic autonome sans supervision medicale
- Usage sur des patients mineurs sans supervision renforcee
- Remplacement du jugement clinique du professionnel de sante

## Documentation technique (Article 11)

### Architecture du modele
- **Algorithme** : TF-IDF (max_features=5000, ngram_range=(1,2)) + LogisticRegression (C=1.0, max_iter=500)
- **Pretraitement** : TF-IDF vectorizer fitte sur train uniquement, tokenisation basique
- **Validation schema** : Pandera sur le DataFrame des textes

### Signatures d'entree et sortie

**Entree** : texte libre (compte-rendu medical synthetique)

**Sortie** :
- `predict(X)` -> int in {0, 1} — 0 = pas d'entite clinique pertinente, 1 = entites detectees
- `predict_proba(X)` -> float[2] — probabilites

## Donnees d'entrainement
**Source** : Textes medicaux synthetiques generes programmatiquement (seed=42). Aucune donnee patient reelle n'est utilisee.

**Volume** : 4 000 observations — train : 2 720 / validation : 480 / test : 800

**Donnees personnelles** : Non — textes entierement synthetiques. En production, les textes reels seraient soumis aux exigences RGPD Art. 9 (donnees de sante).

## Evaluation des performances
- Accuracy : ~0.88
- AUC-ROC : ~0.93
- F1-score : ~0.86
- Precision : ~0.87
- Rappel : ~0.85

## Limites connues
- Modele entraine sur des textes synthetiques — performance reelle a valider sur des textes medicaux authentiques.
- Vocabulaire limite au vocabulaire de la donnee synthetique — pas de generalisation sur des specialites medicales non representees.
- Pas de NER (Named Entity Recognition) granulaire — classification binaire uniquement.

## Controle humain (Article 14)
- Toute extraction doit etre validee par un professionnel de sante avant utilisation clinique.
- Desactivation possible sans delai (kill switch plateforme).
- Chaque prediction est journalisee avec timestamp, hash du texte et version du modele.

## Transparence (Article 13)
- Model card accessible via la plateforme Model Platform.
- Les utilisateurs (professionnels de sante) sont informes de l'utilisation d'un systeme d'IA.

## Tracabilite et gouvernance (Article 12)
- Run MLflow avec identifiant unique et versioning complet.
- Responsable : Octo Technology MLOps Tribe
