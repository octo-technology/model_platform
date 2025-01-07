import streamlit as st

from front.api_interactions.deployed_models import get_deployed_models_list
from front.api_interactions.endpoints import DEPLOYED_MODELS_LIST_ENDPOINT, MODELS_LIST_ENDPOINT
from front.api_interactions.models import deploy_model, get_models_list
from front.api_interactions.projects import get_project_info, get_projects_list

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
            if st.button("Deploy", key=row["Name"]):
                result = deploy_model(row["Name"])
                st.success(result)

else:
    st.warning("No models found or the API is unreachable.")

st.write("### Deployed models")
deployed_models = get_deployed_models_list(DEPLOYED_MODELS_LIST_ENDPOINT)
st.dataframe(deployed_models, use_container_width=True, column_config={"uri": st.column_config.LinkColumn()})
# Vérification de l'état du backend

project_list = get_projects_list()

if len(project_list) == 0 or project_list.empty:
    st.warning("No projects found or the API is unreachable.")
else:
    project_names = project_list["Name"].tolist()
    # Titre
    st.sidebar.title("Select a Project")

    # Menu déroulant pour sélectionner un project
    selected_project = st.sidebar.selectbox("Choose a project", project_names)
    model_info = get_project_info(selected_project)
    # Project infos
    st.sidebar.title("Project infos")
    st.sidebar.dataframe(
        model_info,
    )
