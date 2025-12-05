# Forecasting Demo - Interface Streamlit

Interface de démonstration pour tester des mocks de modèle de forecasting déployés sur la Model Platform.

## 🚀 Lancement rapide

```bash
poetry run streamlit run forecasting_demo_app.py
```

## ⚙️ Configuration

1. **Créer un projet dans la model platform, récupérer l'uri du mlflow associé et mettez à jour la ligne set_uri dans le notebook `forecasting_demo.ipynb`**
2. Déployez les modèles de forecasting (Model A, B, C) via l'interface Model Platform.
3. **Ajoutez les endpoints (sans le /predict)** dans l'onglet prévu à cet effet en haut de l'interface streamlit de l'app.


## 📖 Utilisation

1. Sélectionnez une **date de départ** dans la barre latérale
2. Choisissez un **modèle** (A, B ou C)
3. Cliquez sur "**Générer les prédictions**"
4. Visualisez:
   - Tableau des prédictions pour 21 jours
   - Graphique d'évolution
   - Statistiques (moyenne, total, min, max)

## 🤖 Modèles disponibles

| Modèle | Range (unités/jour) | Usage recommandé |
|--------|---------------------|------------------|
| **Model A** | 100 - 500 | Articles à volume moyen |
| **Model B** | 200 - 800 | Articles à fort volume |
| **Model C** | 50 - 300 | Articles à faible volume |


## 📊 Pour la démonstration

1. **Montrez les métriques et les artefacts** collectés dans MLFlow après le log des modèles via le notebook `forecasting_demo.ipynb`
2. **Testez chaque modèle déployés** en lançant des prédictions via l'interface Streamlit de l'app
3. **Observez les métriques** dans Grafana pendant les prédictions
4. **Montrez les métadonnées** de gouvernance des modèles dans la Model Platform

## 🔗 Liens utiles

- **Frontend Model Platform**: http://model-platform.com
- **Grafana**: http://model-platform.com/grafana/
- **Prometheus**: http://model-platform.com/prometheus/