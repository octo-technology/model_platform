import streamlit as st

from front.api_interactions import endpoints
from front.api_interactions.models import deploy_model
from front.api_interactions.projects import get_project_info


def create_project_selection_sidebar(project_list: list):
    if project_list is not None and (len(project_list) == 0 or project_list.empty):
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


def create_project_model_listing(models_df):
    if models_df is not None and not models_df.empty:
        columns = list(models_df.columns) + ["List Versions"] + ["Actions"]
        col_sizes = [2] * (len(columns) - 1) + [2]  # Dernière colonne plus petite pour le bouton
        col_objects = st.columns(col_sizes)

        # Afficher les en-têtes des colonnes
        for col_obj, col_name in zip(col_objects, columns):
            col_obj.write(f"**{col_name}**")

        # Afficher les lignes du tableau
        for _, row in models_df.iterrows():
            col_objects = st.columns(col_sizes)  # Créer une nouvelle ligne de colonnes

            for col_obj, col_name in zip(col_objects[:-1], models_df.columns):
                col_obj.write(row[col_name])

            # Ajouter le bouton de déploiement
            with col_objects[-1]:
                if st.button("Deploy latest", key="model_listing" + "_" + row["Name"] + "_" + str(row["version"])):
                    action_uri = endpoints.DEPLOY_MODEL_ENDPOINT
                    result = deploy_model(
                        project_name=st.session_state.get("selected_project", "unknown"),
                        model_name=row["Name"],
                        version=row.get("version", "latest"),
                        action_uri=action_uri,
                    )
                    st.success(result)
            with col_objects[-2]:
                if st.button("List Versions", key="list_versions_|" + row["Name"]):
                    st.session_state["tabs"] = ["Project's models", row["Name"] + " versions"]
                    st.session_state["list_versions"] = row["Name"]
                    st.rerun()

    else:
        st.warning("No models found or the API is unreachable.")


def create_deployed_model_listing(models_df):
    if models_df is not None and not models_df.empty:
        columns = list(models_df.columns) + ["Actions"]
        col_sizes = [2] * (len(columns) - 1) + [2]  # Dernière colonne plus petite pour le bouton
        col_objects = st.columns(col_sizes)

        # Afficher les en-têtes des colonnes
        for col_obj, col_name in zip(col_objects, columns):
            col_obj.write(f"**{col_name}**")

        # Afficher les lignes du tableau
        for _, row in models_df.iterrows():
            col_objects = st.columns(col_sizes)  # Créer une nouvelle ligne de colonnes

            for col_obj, col_name in zip(col_objects[:-1], models_df.columns):
                col_obj.write(row[col_name])

            # Ajouter le bouton de déploiement
            with col_objects[-1]:
                if st.button("Undeploy", key="deployed_model_listing" + "_" + row["Name"] + "_" + str(row["version"])):
                    action_uri = endpoints.UNDEPLOY_MODEL_ENDPOINT
                    result = deploy_model(
                        project_name=st.session_state.get("selected_project", "unknown"),
                        model_name=row["Name"],
                        version=row.get("version", "latest"),
                        action_uri=action_uri,
                    )
                    st.success(result)
    else:
        st.warning("No models found or the API is unreachable.")


def create_model_versions_listing(models_df):
    if models_df is not None and not models_df.empty:
        columns = list(models_df.columns) + ["Deploy"]
        col_sizes = [2] * (len(columns) - 1) + [1]  # Dernière colonne plus petite pour le bouton
        col_objects = st.columns(col_sizes)

        # Afficher les en-têtes des colonnes
        for col_obj, col_name in zip(col_objects, columns):
            col_obj.write(f"**{col_name}**")

        # Afficher les lignes du tableau
        for _, row in models_df.iterrows():
            col_objects = st.columns(col_sizes)  # Créer une nouvelle ligne de colonnes

            for col_obj, col_name in zip(col_objects[:-1], models_df.columns):
                col_obj.write(row[col_name])

            # Ajouter le bouton de déploiement
            with col_objects[-1]:
                if st.button("Deploy", key="model_versions_listing" + "_" + row["Name"] + "_" + str(row["version"])):
                    action_uri = endpoints.DEPLOY_MODEL_ENDPOINT
                    result = deploy_model(
                        project_name=st.session_state.get("selected_project", "unknown"),
                        model_name=row["Name"],
                        version=row.get("version", "latest"),
                        action_uri=action_uri,
                    )
                    st.success(result)
    else:
        st.warning("No models found or the API is unreachable.")
