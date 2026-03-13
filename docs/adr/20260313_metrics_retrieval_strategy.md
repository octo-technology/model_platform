# ADR: Stratégie de remontée des métriques de monitoring dans le dashboard unifié

- 📅 Date: 2026/03/13
- 👷 Decision taken by: **Théophile & Philippe** ✅

# Context

- Le dashboard frontend affiche les métriques de tous les modèles déployés (Success Rate, Error Count, Latency, Throughput, System Health, etc.)
- L'infrastructure de monitoring existe déjà : **Prometheus** collecte les métriques + **Grafana** visualise
- Des dashboards Grafana dédiés existent déjà pour chaque modèle déployé
- Le frontend a actuellement des données fakées et doit se connecter à une vraie source
- Il faut éviter de réinventer la roue et s'appuyer sur l'infrastructure existante

**Questions clés:**
- Interroger directement Prometheus via son API REST?
- Utiliser l'API Grafana pour extraire/transformer les données?
- Créer un middleware backend qui centralise et agrège les données?
- Réutiliser les dashboards Grafana existants (embedded or extraction)?

# Considered options 💡

## 1. Requêtes directes à Prometheus (Frontend → Prometheus)

**Plus de détails:**
- Le frontend appelle directement l'API REST de Prometheus sur `/api/v1/query`
- Exemple: `GET http://prometheus:9090/api/v1/query?query=sum(rate(model_requests_total{model_id="xyz"}[7d]))`
- Le backend expose un simple proxy/wrapper si CORS/sécurité est un problème

**✅ Avantages:**
- Direct et simple, pas d'intermédiaire
- Pas d'overhead de transformation
- Requête granulaire exactement ce qu'on veut
- Peut implémenter du caching facilement côté frontend

**🚫 Désavantages:**
- Complexité des requêtes PromQL peut être élevée (jointures multi-métriques, agrégations)
- Exposition directe de Prometheus en production (sécurité)
- Pas de validation/normalisation côté serveur
- Difficult de documenter quelles métriques sont disponibles
- PromQL learning curve pour maintenir les requêtes
- Pas de versioning des requêtes si infra change

---

## 2. Utiliser l'API Grafana pour extraction de données

**Plus de détails:**
- Backend appelle `GET /api/datasources/proxy/<uid>/api/v1/query` sur Grafana
- Ou étend les dashboards Grafana existants avec des annotations/tags pour les retrouver par modèle
- Backend récupère les données transformées via l'API Grafana

**✅ Avantages:**
- Grafana fait déjà l'agrégation correcte (logic centralisée)
- Sécurité: requêtes passe par Grafana qui a auth/RBAC
- Réutilisation des dashboards existants
- Grafana gère déjà la version de Prometheus et compatibilité

**🚫 Désavantages:**
- API Grafana moins documentée pour extraction de données (surtout pannels)
- Overhead: passe par deux couches (Grafana → Prometheus)
- Complexité: need to parse Grafana panels/dashboards
- Les requêtes PromQL complexes restent un problème
- Coûteux en performance (multi-hop)

---

## 3. Backend adapter centralisant (Backend → Prometheus avec wrapper)

**Plus de détails:**
- Créer un `MetricsAdapter` au backend (dans `infrastructure/`)
- Backend expose des endpoints simples: `GET /api/metrics/models/{modelId}`
- Le backend écrit les requêtes PromQL optimisées en dur (ou générées)
- Caching local + refresh periods

**✅ Avantages:**
- Encapsulation: frontend ignore comment les métriques remontent
- Sécurité: Prometheus pas exposé directement
- Logique centralisée: PromQL queries versionées dans le code
- Versioning/évolution facile
- Caching au backend level
- Expose une API claire et documentée
- Transformation/validation possible
- Scalable: peut ajouter du rate limiting, auth par model_id

**🚫 Désavantages:**
- Une couche supplémentaire à maintenir
- Besoin de bien documenter les requêtes PromQL
- Complexité initiale plus élevée
- Need to handle Prometheus unavailability/failures

---

## 4. Hybrid: Grafana embeddings + Prometheus pour les données agrégées

**Plus de détails:**
- Utiliser les dashboards Grafana existants pour les vues détaillées (embedded iframe)
- Mais backend/Prometheus expose des endpoints pour les métriques agrégées (cards au frontend)
- Cohabitation: "quick stats" from API + "deep dive" via Grafana embeddings

**✅ Avantages:**
- Meilleur des deux mondes
- Réutilization des dashboards Grafana (no duplication)
- Fleet overview simple via API
- Drill-down détaillé via Grafana
- Pas de modification aux dashboards existants

**🚫 Désavantages:**
- Complexité: gérer deux sources de données différentes
- Frontend doit orchestrer deux types de requêtes
- Synchronisation possible des états

---

## 5. Custom metrics collector au backend (observer pattern)

**Plus de détails:**
- Backend déploie un sidecar/collector qui agrège les métriques Prometheus
- Store agrégé en mémoire ou petit cache local
- Frontend requête le backend directement
- Similaire à Option 3 mais plus proactif (push vs pull)

**✅ Avantages:**
- Performance: données déjà disponibles (pas de requête Prometheus à chaque fois)
- Agrégations complexes pré-calculées
- Evite le bombardement de Prometheus

**🚫 Désavantages:**
- Complexity: need to maintain a collector process
- State management
- Potential data staleness

---

# Comparison Tableau

| Critère | Option 1 (Direct) | Option 2 (Grafana API) | Option 3 (Backend Adapter) | Option 4 (Hybrid) | Option 5 (Collector) |
|---------|------------------|----------------------|--------------------------|------------------|-------------------|
| **Sécurité** | ⚠️ Faible | ✅ Bonne | ✅ Bonne | ✅ Bonne | ✅ Bonne |
| **Performance** | ✅ Rapide | 🚫 Lente (multi-hop) | ✅ Bonne | 🟡 Mixte | ✅ Très rapide |
| **Maintenance** | 🚫 Complex PromQL | 🚫 Complex | ✅ Centralisée | 🚫 Deux sources | 🚫 Complex |
| **Scalabilité** | 🟡 Depends on PromQL | 🚫 Depends on Grafana | ✅ Bonne | 🟡 Mixte | 🟡 OK |
| **Versioning** | 🚫 Aucun | 🟡 Via Grafana | ✅ Via code | 🟡 Mixte | ✅ Via code |
| **Réutilisation Grafana** | 🚫 Non | ✅ Oui | 🚫 Non | ✅ Oui | 🚫 Non |
| **Time to market** | ✅ Rapide | 🟡 Moyen | 🟡 Moyen | 🟡 Moyen | 🚫 Lent |

---

# Advices

1. **Éviter Option 1 (Direct Prometheus)** en production:
   - La sécurité est un problème
   - PromQL peut devenir très complexe pour les cas multi-modèles
   - Pas de validation côté serveur

2. **Option 2 (Grafana API)** : Valide mais overhead de performance
   - Bonne si tu veux réutiliser les dashboards existants
   - Mais extraction de données de dashboards est pas conçu pour ça

3. **Option 3 (Backend Adapter) est la meilleure pour 80/20**:
   - ✅ Sécurité
   - ✅ Performance
   - ✅ Maintenabilité
   - ✅ Versioning
   - ✅ Évolution future
   - *Recommandé* pour une première itération stable

4. **Option 4 (Hybrid)** : Bonne approche si tu veux explorer les données détaillées
   - Garder les dashboards Grafana pour le "deep dive"
   - Utiliser Option 3 pour les stats rapides au frontend
   - *À considérer pour Phase 2* (après Option 3)

5. **Option 5 (Collector)** : Trop complexe pour le moment, à revisiter future

---

# Decision 🏆

**Validée par:**
- [x] Théophile
- [x] Philippe
- [x] Approuvée

**Décision:** ✅ **Option 3 (Backend Adapter)**

**Justification:**
- Meilleur compromis entre simplicity, sécurité, performance et maintenabilité
- Réduisant la complexité PromQL côté frontend
- Base solide pour évolution future
- Aligne avec le pattern hexagonal du codebase existant (adapter pattern)

**Status:** ACCEPTÉE - Procéder avec Phase 1

---

# Consequences

## À court terme (Phase 1: Backend Adapter)
1. Créer `infrastructure/metrics_adapter.py` (client Prometheus)
2. Ajouter `domain/ports/IMetricsPort` (interface)
3. Ajouter `domain/use_cases/metrics_usecases.py` pour les requêtes métier
4. Ajouter route `GET /api/metrics/models/{modelId}?period=7d` au backend
5. Tester l'intégration avec Prometheus cluster existant

## À moyen terme (Phase 2: Enrichissement)
- Ajouter caching Redis si nécessaire
- Implémenter des requêtes PromQL optimisées par type de métrique
- Ajouter endpoints pour agrégations au niveau fleet (tous modèles)
- Potentiellement intégrer Option 4 (Hybrid) pour deep-dive Grafana

## À long terme
- Monitoring du monitoring: tracker les request latencies à Prometheus
- Ajouter des métriques custom au backend (feedback loops)
- Potentiellement revisiter Option 5 si perf devient un problème

---

♻️ Update: TBD après validation de la décision
