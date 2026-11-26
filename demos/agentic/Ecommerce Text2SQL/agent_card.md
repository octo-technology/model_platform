# Agent Card — ecommerce_text2sql

## Description
Agent conversationnel d'analyse de données e-commerce. Reçoit une question en langage naturel (français), génère et exécute une requête SQL en lecture seule sur la base PostgreSQL e-commerce, puis formule une réponse synthétique.

Architecture : boucle ReAct LangGraph avec deux LLMs (un agent qui génère/utilise les outils, un évaluateur qui critique la réponse finale), bornée par un mécanisme de réflexion (`MAX_REFLECTIONS=2`).

Classifié **risque limité** au sens du Règlement UE 2024/1689 (AI Act) — Article 50 (obligations de transparence pour les systèmes interagissant avec des personnes physiques).

## Niveau de risque AI Act

| Critère | Valeur |
|---|---|
| **Classification** | Risque limité |
| **Justification** | Système d'IA conversationnel destiné à interagir avec des utilisateurs internes pour de l'analyse de données. Aucune décision automatique affectant des personnes physiques. Pas de profilage. Périmètre fonctionnel borné par des outils en lecture seule. |
| **Référence réglementaire** | Article 50 — *"Obligations de transparence pour les fournisseurs et les déployeurs de certains systèmes d'IA"* |
| **Annexe III** | Non applicable — l'agent n'opère dans aucun des domaines à haut risque listés (biométrie, infrastructures critiques, éducation, emploi, accès aux services essentiels, application de la loi, migration, justice, processus démocratiques) |
| **Article 5 (pratiques interdites)** | Non concerné — pas de manipulation cognitive, pas de notation sociale, pas de catégorisation biométrique |

### Impact sur les droits fondamentaux (Article 27)
- **Droit à la transparence** (AI Act Art. 50) : l'utilisateur est informé qu'il interagit avec un système d'IA dans l'interface de chat de la plateforme.
- **Droit à la vie privée** (Charte UE Art. 7, RGPD) : l'agent accède uniquement à la base de données métier e-commerce (produits, commandes, livraisons). Aucune donnée personnelle identifiante directe (PII) n'est exposée dans les réponses. Les requêtes SQL générées peuvent retourner des identifiants techniques (`customer_id`) mais pas de nom, email ou adresse en clair.
- **Protection des données** : la base de données est en lecture seule pour l'agent ; aucune modification possible (voir section Guardrails).

## Usage prévu

### Objectif
Permettre à des utilisateurs métier (analystes, responsables produit, support) d'interroger la base de données e-commerce en langage naturel sans connaître SQL.

### Cas d'usage
1. Requêtes analytiques ad hoc ("Combien de clients ont commandé en mai ?")
2. Préparation de reportings sans passer par l'équipe data
3. Exploration du schéma de données

### Utilisateurs cibles
Collaborateurs internes de l'entreprise e-commerce, authentifiés via la plateforme Model Platform.

### Usages interdits
- Accès direct exposé à des utilisateurs finaux (clients e-commerce) sans contrôle d'accès
- Extraction massive de données personnelles ou de tarification confidentielle
- Utilisation pour des décisions automatisées impactant des personnes (RGPD Art. 22)
- Contournement des permissions de la plateforme via du prompt injection
- Connexion à des bases de données autres que celle e-commerce de référence

## Documentation technique (Article 11)

### Architecture de l'agent

| Composant | Valeur |
|---|---|
| **Framework** | LangGraph (graphe d'états explicite) |
| **Type d'agent** | ReAct avec boucle de réflexion |
| **LLM principal** | `MAMMOUTH_AGENT_MODEL` (défaut : `gpt-4.1`) |
| **LLM évaluateur** | `MAMMOUTH_REFLECT_MODEL` (défaut : `codestral-2508`) |
| **Fournisseur LLM** | Mammouth.ai (API OpenAI-compatible) |
| **Température agent** | `MAMMOUTH_TEMPERATURE` (défaut : `0`) |
| **Température évaluateur** | `0` (déterministe forcé) |
| **Nombre max de réflexions** | `2` |
| **Limite de récursion LangGraph** | `100` |
| **Packaging** | `mlflow.pyfunc.ResponsesAgent` (stateless) |

### Outils disponibles

| Outil | Description | Effets de bord |
|---|---|---|
| `get_schema` | Retourne le schéma complet de la base (tables, colonnes, types) | Lecture seule sur `information_schema` |
| `execute_sql` | Exécute une requête SQL et retourne les résultats formatés | Lecture seule (SELECT/WITH uniquement) |

### Signatures d'entrée et sortie

**Entrée** (`ResponsesAgentRequest`) :
```json
{
  "input": [
    {"role": "user", "content": "Combien de clients ont commandé en mai 2025 ?"},
    {"role": "assistant", "content": "..."}
  ]
}
```
Liste de messages au format OpenAI Responses API. L'historique complet est fourni à chaque requête (l'agent est stateless).

**Sortie** (`ResponsesAgentResponse`) :
```json
{
  "output": [
    {"role": "assistant", "content": "En mai 2025, 1 247 clients distincts ont passé au moins une commande."}
  ]
}
```

### Graphe d'exécution
```
START → agent ──tool_calls──→ tools ──→ agent
              └──no_tool_calls──→ reflect ──approved/max_reached──→ END
                                         └──rejected──→ agent
```

## Guardrails

### Sécurité SQL (lecture seule absolue)
Implémentée dans `security.py:is_read_only_query` :
- Whitelist : la requête doit commencer par `SELECT` ou `WITH`
- Blacklist (regex `\bkeyword\b`) : `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `COPY`, `VACUUM`, `CALL`, `DO`, `EXECUTE`
- Une seule instruction par requête (rejet si `;` n'est pas en fin de chaîne)
- Validation des chaînes de caractères : les mots-clés interdits dans des littéraux (`'...'`, `"..."`) sont ignorés (pré-traitement par regex)

Toute requête échouant à la validation retourne une erreur `"Error: only SELECT/WITH queries are allowed"` au LLM, qui doit alors reformuler ou abandonner.

### Boucle de réflexion (auto-évaluation)
Le LLM évaluateur reçoit la question initiale, les requêtes SQL exécutées avec leurs résultats bruts, et la réponse finale proposée. Il renvoie un JSON :
```json
{"approved": true, "critique": ""}
{"approved": false, "critique": "La réponse ne couvre pas la dimension par catégorie demandée."}
```
- Si `approved=true` : la réponse est validée.
- Si `approved=false` et `reflection_count < MAX_REFLECTIONS` : le LLM principal reçoit la critique en `SystemMessage` interne et régénère.
- Si `reflection_count >= MAX_REFLECTIONS` : la dernière réponse de l'agent est remplacée par un message d'échec courtois (*"Je n'ai pas réussi à trouver des informations pertinentes..."*).

### Prompt système (consignes prioritaires)
Voir `prompts.py:AGENT_SYSTEM_PROMPT`. Points clés :
- Processus obligatoire : `get_schema` puis `execute_sql` avant toute réponse chiffrée.
- **Interdiction d'hallucination** : tout chiffre dans la réponse doit provenir d'une requête SQL exécutée dans le même tour.
- Réponses en français, ton professionnel, structure : chiffre clé → suggestion.
- Les valeurs en base sont en anglais (statuts de commande, livraison, retour, ticket) — interdiction de les traduire dans les `WHERE`.

### Validation de domaine d'entrée
L'agent ne refuse pas explicitement les questions hors domaine, mais s'appuie sur le system prompt pour rester dans le périmètre e-commerce. Une question manifestement hors sujet déclenchera soit `get_schema` (par défaut), soit une réponse indiquant l'absence d'information disponible.

## Modèles et prompts utilisés

### LLMs (3rd party)
- **Agent principal** : `gpt-4.1` via API Mammouth.ai — modèle généraliste utilisé pour la planification, la génération SQL et la rédaction de la réponse.
- **Évaluateur** : `codestral-2508` via API Mammouth.ai — modèle orienté code, utilisé pour critiquer la pertinence et la cohérence SQL/réponse.
- **Fournisseur** : Mammouth.ai (proxy multi-modèles, conformité RGPD assurée par le fournisseur — voir DPA Mammouth).

### Prompts versionnés
Les prompts sont versionnés dans le code source (`prompts.py`) et leur hash est tracé dans chaque run MLflow.

| Prompt | Rôle |
|---|---|
| `AGENT_SYSTEM_PROMPT` | Définit le processus, les règles SQL et le format de réponse de l'agent principal |
| `REFLECTION_SYSTEM_PROMPT` | Définit le contrat JSON et les critères d'évaluation de l'évaluateur |

## Données accédées

**Source** : base PostgreSQL e-commerce (transactions, produits, commandes, livraisons, retours, tickets support).

**Volume** : variable selon l'environnement (dev / staging / prod).

**Langue** : libellés en anglais en base (statuts, types). Données textuelles libres (commentaires support, descriptions produits) potentiellement multilingues.

**Données personnelles** :
- L'agent peut accéder à des tables contenant des identifiants techniques (`customer_id`, `order_id`).
- Les réponses doivent éviter d'exposer des PII directes (nom, email, adresse) sauf si explicitement demandé par un utilisateur autorisé.
- Aucune donnée n'est conservée par l'agent entre les requêtes (stateless).

**Données non accédées** : tables d'authentification, secrets, logs d'audit système.

## Évaluation des performances

### Métriques techniques
À évaluer sur un jeu de questions de test (à constituer) :
- **Exactitude SQL** : taux de requêtes générées syntaxiquement valides
- **Exactitude métier** : taux de réponses sémantiquement correctes (validation humaine sur échantillon)
- **Taux de réflexion approuvée du premier coup** (sans retry)
- **Taux d'échec** (réponses où `MAX_REFLECTIONS` est atteint sans approbation)
- **Latence moyenne** par tour (LLM + SQL + reflection)

### Tests qualitatifs recommandés
- Questions simples (`COUNT`, `SUM` mono-table) — niveau attendu : 100%
- Jointures inter-tables avec agrégation — niveau attendu : ≥ 90%
- Questions ambiguës — l'agent doit demander une clarification plutôt qu'inventer
- Questions hors sujet — l'agent doit décliner sans halluciner de chiffre

## Limites connues
- **Pas de mémoire long terme** : l'historique de conversation est fourni par l'appelant à chaque requête ; l'agent ne maintient aucun état entre les sessions.
- **Dépendance LLM externe** : indisponibilité de l'API Mammouth.ai = indisponibilité de l'agent. Aucun fallback local prévu.
- **Coût et latence** : chaque tour utilise potentiellement plusieurs appels LLM (agent + tools + reflection). Coût par tour ≈ 1-3 appels LLM payants.
- **Garantie SQL imparfaite** : la validation de `is_read_only_query` est syntaxique. Des requêtes complexes valides mais coûteuses (joins massifs, sous-requêtes corrélées sur grosses tables) peuvent dégrader la DB de production.
- **Pas de limites de pagination** : les résultats sont tronqués à 500 lignes par `format_rows`, mais une requête SQL peut scanner la totalité d'une table avant la troncature applicative.
- **Détection d'injection prompt** : aucune protection spécifique contre l'injection via le contenu des données retournées (ex: une description produit contenant des instructions pour l'agent).

## Contrôle humain (Article 14)
- L'agent est un outil d'**aide à l'analyse**, pas un décideur. Aucune action de l'agent n'engage l'organisation envers un tiers.
- Désactivation possible par l'administrateur de la plateforme (via le contrôle de version MLflow + la liste des agents actifs).
- Chaque appel à l'agent est journalisé dans MLflow (trace LangChain auto-loggée) avec : timestamp, question utilisateur, requêtes SQL exécutées, réponse finale, version de l'agent et version des prompts.
- L'utilisateur peut signaler une réponse incorrecte via l'interface de chat — les signalements alimentent le jeu de test de régression.
- Procédure de modification : toute évolution des prompts ou du graphe nécessite (a) une nouvelle version MLflow, (b) une réévaluation de conformité, (c) une validation sur le jeu de test avant promotion en production.

## Transparence et information utilisateur (Article 13 et 50)
- **Information utilisateur** : l'interface de chat affiche explicitement que l'interlocuteur est un agent IA (conformité Art. 50 §1).
- **Limites communiquées** : l'utilisateur est informé que l'agent peut se tromper et qu'il convient de vérifier les chiffres critiques par une seconde requête ou auprès de l'équipe data.
- **Périmètre fonctionnel** : la documentation utilisateur précise que l'agent n'a accès qu'à la base e-commerce et qu'il ne peut pas modifier les données.
- **Documentation accessible** : la présente agent card est mise à disposition des utilisateurs via la plateforme Model Platform.

## Explicabilité
- **Traces MLflow** : chaque tour de conversation produit un span MLflow contenant l'arbre d'appels LLM, les requêtes SQL exécutées et leurs résultats bruts. Permet de comprendre a posteriori comment l'agent est arrivé à une réponse.
- **Requêtes SQL exposables** : sur demande explicite, l'agent peut inclure le SQL exécuté dans sa réponse (utile pour audit ou pour l'équipe data).
- **Critique de l'évaluateur** : la critique du LLM évaluateur est conservée dans la trace en cas de retry, permettant de comprendre les corrections appliquées.

## Robustesse (Article 15)
### Mécanismes en place
1. **Validation SQL stricte** (`security.py`) : rejet des opérations en écriture, des instructions multiples, des mots-clés dangereux.
2. **Réflexion avec garde-fou** : `MAX_REFLECTIONS=2` empêche une boucle infinie d'auto-correction.
3. **Limite de récursion LangGraph** : `recursion_limit=100` borne le nombre total de transitions dans le graphe.
4. **Échappement des `%`** : `database_utils.execute_query` échappe les `%` littéraux pour éviter une mauvaise interprétation par psycopg.
5. **Erreurs SQL retournées au LLM** : une erreur SQL n'interrompt pas l'agent, elle est passée comme `ToolMessage` au LLM qui peut corriger.

### Mesures de cybersécurité
- L'agent est servi via MLflow Model Serving avec authentification JWT et HTTPS (assuré par la plateforme).
- Les credentials DB et API LLM sont fournis via variables d'environnement (Kubernetes secrets), jamais commitées.
- Aucune écriture sur la base e-commerce (whitelist `SELECT`/`WITH` + blacklist des DML/DDL).
- Aucune exécution de code arbitraire — l'agent ne fait que générer du texte (SQL) qui passe par la validation avant exécution.

### Risques résiduels
- **Prompt injection via contenu des données** : un attaquant pouvant insérer du texte dans une table accessible (ex: description produit) pourrait tenter d'instrucer l'agent. Mitigation : surveillance des patterns suspects dans les traces.
- **DoS via requêtes coûteuses** : un utilisateur malveillant pourrait formuler des questions provoquant des requêtes SQL très lourdes. Mitigation : timeout côté DB, monitoring des requêtes longues.

## Traçabilité et gouvernance (Article 12)
- **Run MLflow** : chaque conversation produit une trace MLflow identifiée par un `run_id` avec horodatage précis.
- **Versioning** : chaque déploiement de l'agent produit une nouvelle version dans le MLflow Model Registry (tag `model_type=agent`).
- **Responsable** : louis.delmas (Stage Octo Technology) — encadrement philippe.stepniewski (MLOps Tribe, Octo Technology).
- **Dépôt de code** : `model_platform` (branche `feat/AgentInfoAndDB` au moment de cette version).
- **Journalisation** : tous les événements (déploiement, conversations, désactivation) sont journalisés dans la plateforme Model Platform.
- **Chaîne de responsabilité** : Développeur (implémentation et tests) → Risk Officer (validation conformité) → Administrateur plateforme (déploiement et supervision).
- **Procédure de modification** : toute modification des prompts, du graphe ou des LLMs utilisés nécessite (a) une nouvelle version MLflow, (b) une réévaluation de conformité (déterministe + LLM), (c) une validation sur le jeu de test de régression.

## Système de gestion qualité (Article 17)
- **Processus de développement** : code versionné, tests unitaires sur la validation SQL et la conversion de messages.
- **Processus de validation** : évaluation déterministe automatisée (présence des champs `agent_card`, `risk_level`, `tools`, etc.) + revue AI Act par LLM.
- **Processus de déploiement** : via la plateforme Model Platform avec contrôle d'accès, versioning MLflow et kill switch.
- **Documentation** : agent card maintenue à jour à chaque version, traces MLflow conservées au moins 12 mois.

## Surveillance post-déploiement (Article 72)

### Plan de surveillance continue
| Indicateur | Fréquence | Seuil d'alerte | Responsable | Action |
|---|---|---|---|---|
| Taux de réflexion approuvée 1er essai | Hebdomadaire | < 70% | ML Engineer | Revue des prompts / tests |
| Taux d'échec (MAX_REFLECTIONS atteint) | Hebdomadaire | > 10% | ML Engineer | Investigation des questions échouées |
| Latence moyenne par tour | Quotidien | > 30s | ML Engineer | Alerte + investigation |
| Coût LLM moyen par session | Hebdomadaire | Dérive > 30% | Product Owner | Revue d'usage |
| Requêtes SQL rejetées | Quotidien | > 5% des appels | ML Engineer | Revue des prompts |
| Signalements utilisateurs | Continu | Tout signalement critique | Risk Officer | Revue cas par cas |

### Procédures opérationnelles
- **Mise à jour des prompts** : suit le workflow de version MLflow normal — nouvelle version, validation, déploiement.
- **Retrait d'urgence** : l'administrateur plateforme peut désactiver l'agent immédiatement via le kill switch.
- **Reporting** : rapport mensuel d'usage et de conformité transmis au Risk Officer.
- **Gestion des incidents** : tout incident (hallucination critique, fuite de données, indisponibilité prolongée) est documenté et tracé dans la plateforme.

## Déclaration de conformité et enregistrement UE (Article 49)
- **Statut** : non applicable pour un système classé **risque limité**. Les obligations d'enregistrement UE de l'Art. 49 concernent les systèmes à haut risque.
- **Obligations applicables** : transparence Art. 50 (information de l'utilisateur qu'il interagit avec une IA) — assurée par l'interface de chat de la plateforme.
- **Marquage CE** : non applicable.
- **Responsable conformité** : Risk Officer.
