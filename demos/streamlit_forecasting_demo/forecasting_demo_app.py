"""
Model Platform Demo - Streamlit Interface for Sales Forecasting

This application provides an interactive interface to test the 3 forecasting models
(model A, B, C) deployed on the Model Platform.
"""

import time
from datetime import date

import pandas as pd
import requests
import streamlit as st

# Page configuration
st.set_page_config(page_title="Model Platform Demo - Prédictions de ventes", page_icon="📊", layout="wide")

# Title and description
st.title("📊 Model Platform - Prédictions de ventes")
st.markdown("---")
st.markdown("""
Cette interface permet de tester les 3 modèles de forecasting déployés sur la **Model Platform**.
Chaque modèle prédit les quantités de ventes pour les **21 jours suivants** (3 semaines).
""")

# Endpoint configuration (collapsible)
with st.expander("🔧 Configuration des endpoints", expanded=False):
    st.markdown("Modifiez les URLs complètes des endpoints si nécessaire :")

    endpoint_model_A = st.text_input(
        "🤖 URL endpoint model_A",
        value="http://model-platform.com/deploy/my-project/my-project-model-a-1-deployment-XXXXX",
        help="URL de base de l'endpoint pour model_A (sans /predict)",
    )

    endpoint_model_B = st.text_input(
        "🤖 URL endpoint model_B",
        value="http://model-platform.com/deploy/my-project/my-project-model-b-1-deployment-XXXXX",
        help="URL de base de l'endpoint pour model_B (sans /predict)",
    )

    endpoint_model_C = st.text_input(
        "🤖 URL endpoint model_C",
        value="http://model-platform.com/deploy/my-project/my-project-model-c-1-deployment-XXXXX",
        help="URL de base de l'endpoint pour model_C (sans /predict)",
    )

    st.caption(
        '💡 Pour obtenir les noms de déploiement : `poetry run mp projects list-deployed-models "nom de mon projet"`'
    )

st.markdown("---")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    st.markdown("### 📅 Date de départ")
    selected_date = st.date_input(
        "Choisir le jour de départ",
        value=date.today(),
        help="Sélectionner le jour à partir duquel prédire les 3 prochaines semaines",
        label_visibility="collapsed",
    )

    st.markdown("### 🤖 Modèle")
    model_choice = st.selectbox(
        "Choisir le modèle",
        options=["model_A", "model_B", "model_C"],
        help="Sélectionner le modèle de forecasting à utiliser",
        label_visibility="collapsed",
    )

    # Model descriptions
    model_descriptions = {
        "model_A": "**Range:** 100-500 unités/jour  \n**Usage:** Articles à volume moyen",
        "model_B": "**Range:** 200-800 unités/jour  \n**Usage:** Articles à fort volume",
        "model_C": "**Range:** 50-300 unités/jour  \n**Usage:** Articles à faible volume",
    }

    with st.expander("ℹ️ Détails du modèle"):
        st.markdown(model_descriptions[model_choice])

    st.markdown("---")

    # Predict button
    predict_button = st.button("🔮 Générer les prédictions", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("💡 **Astuce:** Changez de modèle pour comparer les prédictions")

# Main content area
if predict_button:
    # Get endpoint URL from inputs
    endpoint_mapping = {"model_A": endpoint_model_A, "model_B": endpoint_model_B, "model_C": endpoint_model_C}

    base_url = endpoint_mapping[model_choice]
    url = f"{base_url}/predict" if not base_url.endswith("/predict") else base_url

    # Prepare payload
    payload = {"inputs": {"date": selected_date.strftime("%Y-%m-%d")}}

    # Make prediction
    try:
        with st.spinner(f"🔄 Prédiction en cours avec **{model_choice}**..."):
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            elapsed_time = time.time() - start_time

            # Parse response
            result = response.json()
            predictions_df = pd.DataFrame(result["outputs"])
            predictions_df["date"] = pd.to_datetime(predictions_df["date"])

            # Success message
            st.success(f"✅ Prédiction réussie avec **{model_choice}** en {elapsed_time:.2f}s")

            # Display results in columns
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("📊 Tableau des prédictions")

                # Format and display dataframe
                display_df = predictions_df.copy()
                display_df["date"] = display_df["date"].dt.strftime("%d/%m/%Y")
                display_df.columns = ["Date", "Ventes prédites"]

                st.dataframe(
                    display_df.style.format({"Ventes prédites": "{:.0f}"}), use_container_width=True, height=400
                )

                # Statistics
                st.markdown("### 📈 Statistiques")

                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric(
                        "Moyenne",
                        f"{predictions_df['predicted_sales'].mean():.0f}",
                        help="Moyenne des ventes prédites sur 21 jours",
                    )
                with metric_col2:
                    st.metric(
                        "Total (3 sem.)",
                        f"{predictions_df['predicted_sales'].sum():.0f}",
                        help="Total des ventes prédites sur 3 semaines",
                    )

                metric_col3, metric_col4 = st.columns(2)
                with metric_col3:
                    st.metric(
                        "Minimum", f"{predictions_df['predicted_sales'].min():.0f}", help="Vente minimale prédite"
                    )
                with metric_col4:
                    st.metric(
                        "Maximum", f"{predictions_df['predicted_sales'].max():.0f}", help="Vente maximale prédite"
                    )

            with col2:
                st.subheader("📈 Graphique des prédictions")

                # Line chart
                chart_data = predictions_df.set_index("date")["predicted_sales"]
                st.line_chart(chart_data, use_container_width=True, height=400)

                # Additional info
                st.info(f"""
                **Période de prédiction:** {predictions_df["date"].min().strftime("%d/%m/%Y")}
                → {predictions_df["date"].max().strftime("%d/%m/%Y")}

                **Modèle utilisé:** {model_choice}

                **Temps de réponse:** {elapsed_time:.2f}s
                """)

    except requests.exceptions.ConnectionError:
        st.error("""
        ❌ **Erreur de connexion**

        Impossible de se connecter au modèle. Vérifiez que:
        - Le modèle est bien déployé
        - `minikube tunnel` est actif
        - L'URL est correcte
        """)

    except requests.exceptions.Timeout:
        st.error("""
        ⏱️ **Timeout**

        La requête a pris trop de temps. Le modèle est peut-être en cours de démarrage.
        Réessayez dans quelques instants.
        """)

    except requests.exceptions.HTTPError as e:
        st.error(f"""
        ❌ **Erreur HTTP {response.status_code}**

        Le serveur a renvoyé une erreur: {str(e)}

        **Détails de la réponse:**
        ```
        {response.text}
        ```
        """)

    except Exception as e:
        st.error(f"""
        ❌ **Erreur inattendue**

        {str(e)}
        """)
        st.exception(e)

else:
    # Initial state - show instructions
    st.info("""
    ### 👈 Pour commencer

    1. Sélectionnez une **date de départ** dans la barre latérale
    2. Choisissez un **modèle** (A, B ou C)
    3. Cliquez sur **"Générer les prédictions"**

    ### 📊 Ce que vous obtiendrez

    - Un tableau détaillé des prédictions pour 21 jours
    - Un graphique visualisant l'évolution des ventes
    - Des statistiques clés (moyenne, total, min, max)
    """)

    # Show model comparison
    st.markdown("### 🤖 Comparaison des modèles")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **model_A**
        - Range: 100-500 unités
        - Idéal pour articles à volume moyen
        - MAE: ~35 unités
        """)

    with col2:
        st.markdown("""
        **model_B**
        - Range: 200-800 unités
        - Idéal pour articles à fort volume
        - MAE: ~45 unités
        """)

    with col3:
        st.markdown("""
        **model_C**
        - Range: 50-300 unités
        - Idéal pour articles à faible volume
        - MAE: ~27 unités
        """)

# Footer
st.markdown("---")
st.caption("📊 Model Platform Demo | Powered by MLflow & Kubernetes")
