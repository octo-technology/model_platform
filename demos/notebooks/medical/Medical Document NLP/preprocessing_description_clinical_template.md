# Description du pretraitement des donnees — clinical_entity_extractor

## Source des donnees
Textes medicaux synthetiques generes programmatiquement pour la demonstration.
Aucune donnee patient reelle n'est utilisee dans ce notebook.

## Schema de donnees (Pandera)
- Schema : `{schema_name}`
- Statut de validation : **{pandera_status}** ({pandera_errors} erreur(s))

## Variables d'entree
| Variable | Description | Type | Contrainte Pandera |
|---|---|---|---|
| text | Texte du compte-rendu medical | str | non nul, longueur >= 10 |
| text_length | Longueur du texte (caracteres) | int | in_range(10, 5000) |
| word_count | Nombre de mots | int | in_range(2, 1000) |
| has_negation | Presence de termes de negation | int | isin([0, 1]) |

## Etapes de pretraitement
1. Validation du schema Pandera sur les features derivees
2. Split stratifie : 68% train / 12% validation / 20% test
3. Vectorisation TF-IDF (max_features=5000, ngram_range=(1,2)) fittee sur le train uniquement
4. Pas de normalisation additionnelle (TF-IDF produit des vecteurs normalises)

## Attributs proteges
Aucun attribut protege dans les features derivees. En production, les textes reels constitueraient des donnees de sante (RGPD Art. 9).
