import streamlit as st

from front.api_interactions import endpoints
from front.api_interactions.deployed_models import get_build_status
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


def build_model_version_listing(models_df, name="model_listing", elements_to_add=None):
    if models_df is not None and not models_df.empty:
        columns = list(models_df.columns) + elements_to_add
        col_sizes = [2] * (len(columns) + len(elements_to_add))
        col_objects = st.columns(col_sizes)
        for col_obj, col_name in zip(col_objects, columns):
            col_obj.write(f"**{col_name}**")
        for _, row in models_df.iterrows():
            col_objects = st.columns(col_sizes)
            for col_obj, col_name in zip(col_objects, columns):
                if col_name in models_df.columns:
                    col_obj.write(row[col_name])
                elif col_name in ["Deploy", "Deploy latest"]:
                    with col_obj:
                        build_deploy_button(name, row)
                elif col_name == "List versions":
                    with col_obj:
                        build_list_versions_button(name, row)
                elif col_name == "Undeploy":
                    with col_obj:
                        build_undeploy_button(name, row)
            with col_objects[-1]:
                build_status(name, row)

    else:
        st.warning("No models found or the API is unreachable.")


def build_deploy_button(component_name: str, row: dict):
    key = "_".join([str(value) for key, value in row.items()])
    state_task_id_key = "task_id_" + key
    button_key = component_name + key
    if state_task_id_key not in st.session_state or st.session_state[state_task_id_key] is None:
        if st.button("Deploy", key=button_key):
            action_uri = endpoints.DEPLOY_MODEL_ENDPOINT
            result = deploy_model(
                project_name=st.session_state.get("selected_project", "unknown"),
                model_name=row["Name"],
                version=row.get("version", "latest"),
                action_uri=action_uri,
            )
            task_id = result["task_id"]
            st.session_state[state_task_id_key] = task_id


def build_status(component_name: str, row: dict):
    key = "_".join([str(value) for key, value in row.items()])
    state_task_id_key = "task_id_" + key
    if state_task_id_key in st.session_state and st.session_state[state_task_id_key] is not None:
        task_id = st.session_state[state_task_id_key]
        status = get_build_status(st.session_state.get("selected_project", "unknown"), task_id)
        if "PROGRESS" in status:
            st.status("Deploying")
        elif "COMPLETED" in status:
            st.success("Deployed")
            st.session_state[state_task_id_key] = None
        elif "FAILED" in status:
            st.error("Failed to deploy")
            st.session_state[state_task_id_key] = None


def build_list_versions_button(component_name: str, row: dict):
    if st.button("List Versions", key=component_name + row["Name"]):
        st.session_state["tabs"] = ["Project's models", row["Name"] + " versions"]
        st.session_state["list_versions"] = row["Name"]
        st.rerun()


def build_undeploy_button(component_name: str, row: dict):
    key = component_name + "_".join([str(value) for key, value in row.items()])
    if st.button("Undeploy", key=key):
        action_uri = endpoints.UNDEPLOY_MODEL_ENDPOINT
        deploy_model(
            project_name=st.session_state.get("selected_project", "unknown"),
            model_name=row["Name"],
            version=row.get("version", "latest"),
            action_uri=action_uri,
        )
        st.success("Action performed")
