import pandas as pd
import streamlit as st

from front.api_interactions.deployed_models import get_deployed_models_list
from front.api_interactions.endpoints import MODELS_LIST_ENDPOINT, DEPLOYED_MODELS_LIST_ENDPOINT, HEALTH_ENDPOINT
from front.api_interactions.health import check_backend_health
from front.api_interactions.models import get_models_list, deploy_model

models = get_models_list(MODELS_LIST_ENDPOINT)
st.title("Model Platform")

if models is not None:
    st.write("#### Available models")

    # Créer l'entête du tableau manuellement pour les colonnes
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
    col1.write("**Name**")
    col2.write("**Creation Date**")
    col3.write("**Aliases**")
    col4.write("**Versions**")
    col5.write("**Deploy**")

    # Affichage des lignes du tableau
    for index, row in models.iterrows():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])  # Colonne pour le bouton
        col1.write(row["Name"])
        col2.write(row["Creation Date"])
        col3.write(row["Aliases"])
        col4.write(row["Versions"])

        # Afficher le bouton de déploiement
        with col5:
            if st.button(f"Deploy", key=row['Name']):
                result = deploy_model(row['Name'])
                st.success(result)

else:
    st.warning("No models found or the API is unreachable.")

st.write("### Deployed models")
deployed_models = get_deployed_models_list(DEPLOYED_MODELS_LIST_ENDPOINT)
st.dataframe(deployed_models, use_container_width=True)
# Vérification de l'état du backend


project_names = ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta"]

# Titre
st.sidebar.title("Select a Project")

# Menu déroulant pour sélectionner un projet
selected_project = st.sidebar.selectbox("Choose a project", project_names)

# Project infos
st.sidebar.title("Project infos")
project_card = pd.DataFrame({
    "Project name": selected_project,
    "Owner": "The best team ever",
    "Scope": "A project to revolutionize IA projects",
    "Data perimeter": "All data on earth regarding our clients",
}, index=["Infos"]).T
st.sidebar.dataframe(project_card, )
st.sidebar.title("Backend status")

# Affichage de l'état avec une pastille
status_colors = {
    "healthy": "🟢",
    "unhealthy": "🟠",
    "unreachable": "🔴"
}
status = check_backend_health(HEALTH_ENDPOINT)
st.sidebar.markdown(f"{status_colors[status]} {status.capitalize()}")
