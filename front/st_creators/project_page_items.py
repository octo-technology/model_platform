import pandas as pd
import streamlit as st

from front.api_interactions.models import deploy_model
from front.api_interactions.projects import get_project_info


def create_project_selection_sidebar(project_list: list):
    if len(project_list) == 0 or project_list.empty:
        st.warning("No projects found or the API is unreachable.")
    else:
        project_names = project_list["Name"].tolist()
        # Titre
        st.sidebar.title("Select a Project")

        # Menu déroulant pour sélectionner un project
        selected_project = st.sidebar.selectbox("Choose a project", project_names)
        st.session_state["selected_project"] = selected_project
        model_info = get_project_info(selected_project)
        # Project infos
        st.sidebar.title("Project infos")
        st.sidebar.dataframe(
            model_info,
        )


def create_project_model_listing(models: list):
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


def create_project_deployed_models_listing(deployed_models: pd.DataFrame):
    st.write("### Deployed models")
    if deployed_models is None:
        st.warning("No deployed models found or the API is unreachable.")
    else:
        st.dataframe(deployed_models, use_container_width=True, column_config={"uri": st.column_config.LinkColumn()})
