# Agent Card — weather_assistant

## Description
Assistant conversationnel météo. Reçoit une question en langage naturel (français), récupère la météo actuelle d'une ville via une API tierce (OpenWeatherMap) et formule une réponse synthétique. Peut aussi convertir une température entre Celsius/Fahrenheit/Kelvin.

Architecture : boucle ReAct LangGraph simple, sans mécanisme de réflexion — volontairement plus simple que l'agent Text2SQL, pour servir de deuxième cas d'usage validant la généricité du pipeline enregistrement/déploiement/gouvernance de la plateforme.

Classifié **risque minimal** au sens du Règlement UE 2024/1689 (AI Act) — aucune interaction affectant des personnes physiques, aucune donnée personnelle traitée.

## Niveau de risque AI Act

| Critère | Valeur |
|---|---|
| **Classification** | Risque minimal |
| **Justification** | Système d'IA fournissant une information factuelle publique (météo). Aucune décision automatique, aucun profilage, aucune donnée personnelle traitée. |
| **Référence réglementaire** | Aucune obligation spécifique applicable (hors bonnes pratiques générales de transparence, Art. 50, appliquées par convention plateforme) |
| **Annexe III** | Non applicable |
| **Article 5 (pratiques interdites)** | Non concerné |

### Impact sur les droits fondamentaux
- **Vie privée** : aucune donnée personnelle collectée ou traitée ; seule une ville (donnée géographique publique) est transmise à l'API météo tierce.

## Usage prévu

### Objectif
Démontrer, avec un deuxième agent volontairement différent (pas de DB, pas de boucle de réflexion, secret dédié), que la plateforme peut enregistrer/déployer/gouverner n'importe quel agent respectant la convention `agent.py:create_graph`/`ResponsesAgent`, sans modification du code plateforme.

### Cas d'usage
1. Question météo ponctuelle sur une ville
2. Conversion d'unité de température

### Utilisateurs cibles
Utilisateurs internes de démonstration de la Model Platform.

### Usages interdits
- Utilisation comme source météo pour des décisions critiques (sécurité, agriculture, aviation)
- Exposition directe à des utilisateurs finaux sans avertissement sur la fiabilité des données tierces

## Documentation technique (Article 11)

### Architecture de l'agent

| Composant | Valeur |
|---|---|
| **Framework** | LangGraph (graphe d'états explicite) |
| **Type d'agent** | ReAct simple (sans réflexion) |
| **LLM** | `MAMMOUTH_AGENT_MODEL` (défaut : `gpt-4.1`) |
| **Fournisseur LLM** | Mammouth.ai (API OpenAI-compatible) |
| **Température** | `MAMMOUTH_TEMPERATURE` (défaut : `0`) |
| **Limite de récursion LangGraph** | `25` |
| **Packaging** | `mlflow.pyfunc.ResponsesAgent` (stateless) |

### Outils disponibles

| Outil | Description | Effets de bord |
|---|---|---|
| `get_current_weather` | Appelle l'API OpenWeatherMap pour une ville | Appel réseau externe en lecture seule |
| `convert_temperature` | Conversion Celsius/Fahrenheit/Kelvin | Aucun (calcul pur) |

### Graphe d'exécution
```
START → agent ──tool_calls──→ tools ──→ agent
              └──no_tool_calls──→ END
```

## Guardrails
- **Appel externe en lecture seule** : `get_current_weather` n'effectue qu'un `GET` vers l'API météo ; aucune écriture possible.
- **Limite de récursion** : `recursion_limit=25` borne le nombre de transitions dans le graphe.
- **Erreurs gérées explicitement** : ville introuvable ou API indisponible retournent un message d'erreur au LLM plutôt que de faire échouer l'agent.
- **Secret dédié** : la clé `WEATHER_API_KEY` est injectée via K8s Secret au déploiement, jamais en dur dans le code/la config/MLflow.

## Données accédées
**Source** : API météo tierce (OpenWeatherMap). Seule donnée transmise : le nom de ville fourni par l'utilisateur.
**Données personnelles** : aucune.

## Limites connues
- **Dépendance à deux APIs externes** : LLM (Mammouth) et météo (OpenWeatherMap) — indisponibilité de l'une ou l'autre dégrade l'agent.
- **Pas de mémoire** : agent stateless, l'historique est fourni par l'appelant à chaque requête.
- **Fiabilité des données météo** : dépend entièrement du fournisseur tiers, aucune vérification croisée.

## Contrôle humain (Article 14)
- Agent d'information, aucune action n'engage l'organisation envers un tiers.
- Désactivation possible par l'administrateur de la plateforme (kill switch, comme tout agent).
- Chaque appel est journalisé dans MLflow (trace LangChain auto-loggée).

## Traçabilité et gouvernance (Article 12)
- **Run MLflow** : chaque conversation produit une trace MLflow identifiée par un `run_id`.
- **Versioning** : chaque déploiement produit une nouvelle version MLflow (tag `model_type=agent`).
- **Responsable** : louis.delmas (Stage Octo Technology).
- **Dépôt de code** : `model_platform`, `demos/agentic/Weather Assistant/`.
