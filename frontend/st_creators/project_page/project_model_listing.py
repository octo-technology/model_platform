import streamlit as st

from frontend.api_interactions import endpoints
from frontend.api_interactions.deployed_models import get_build_status, get_model, undeploy_model
from frontend.api_interactions.models import deploy_model, get_model_versions_list


# Columns to hide from display but keep accessible in row data
HIDDEN_COLUMNS = ["dashboard_url"]


def build_model_version_listing(models_df, project_name: str, component_name="model_listing", elements_to_add=None):
    if models_df is not None and not models_df.empty:
        columns = [col for col in models_df.columns if col not in HIDDEN_COLUMNS] + elements_to_add
        col_sizes = [2] * (len(columns) + len(elements_to_add))
        col_objects = st.columns(col_sizes)
        for col_obj, col_name in zip(col_objects, columns):
            col_obj.write(f"**{col_name}**")
        for _, row in models_df.iterrows():
            col_objects = st.columns(col_sizes)
            for col_obj, col_name in zip(col_objects, columns):
                if col_name in models_df.columns:
                    if col_name in ["Version"] and component_name == "available_models":
                        with col_obj:
                            build_model_versions_sel(project_name, component_name, row["Name"])
                    elif col_name in ["Url"] and component_name == "deployed_models":
                        with col_obj:
                            st.link_button(":blue[Deployment endpoint]", url=row[col_name], type="tertiary")
                    else:
                        col_obj.write(row[col_name])
                elif col_name in ["Action"] and component_name == "available_models":
                    with col_obj:
                        build_deploy_button(project_name, component_name, row)
                        build_status(project_name, row)
                elif col_name in ["Dashboard"] and component_name == "deployed_models":
                    with col_obj:
                        build_dashboard_button(row)
                elif col_name in ["Action"] and component_name == "deployed_models":
                    with col_obj:
                        build_undeploy_button(project_name, component_name, row)
                elif col_name in ["Action"] and component_name == "public_models":
                    with col_obj:
                        build_get_button(project_name, component_name, row)


def build_model_versions_sel(project_name: str, component_name: str, model_name: str):
    st.selectbox(
        label="",
        options=get_model_versions_list(project_name=project_name, model_name=model_name),
        key=f"{component_name}_version_{project_name}_{model_name}",
        index=0,
        label_visibility="collapsed",
    )


def build_deploy_button(project_name: str, component_name: str, row: dict):
    key = "_".join([str(value) for key, value in row.items()])
    state_task_id_key = "task_id_" + key
    button_key = component_name + key
    if state_task_id_key not in st.session_state or st.session_state[state_task_id_key] is None:
        if st.button("Deploy", key=button_key, type="primary"):
            action_uri = endpoints.DEPLOY_MODEL_ENDPOINT
            model_name = row["Name"]
            selected_version_key = f"{component_name}_version_{project_name}_{model_name}"
            selected_version = st.session_state.get(selected_version_key, None)
            result = deploy_model(
                project_name=project_name,
                model_name=row["Name"],
                version=selected_version,
                action_uri=action_uri,
            )
            task_id = result["task_id"]
            st.session_state[state_task_id_key] = task_id
            st.rerun()


def build_status(project_name: str, row: dict):
    key = "_".join([str(value) for key, value in row.items()])
    state_task_id_key = "task_id_" + key
    if state_task_id_key in st.session_state and st.session_state[state_task_id_key] is not None:
        task_id = st.session_state[state_task_id_key]
        status = get_build_status(project_name, task_id)
        if "PROGRESS" in status:
            st.status("Deploying")
        elif "COMPLETED" in status:
            st.session_state["action_model_deployment_ok"] = True
            st.session_state[state_task_id_key] = None
        elif "FAILED" in status:
            st.session_state["action_model_deployment_ok"] = False
            st.session_state[state_task_id_key] = None


def build_undeploy_button(project_name: str, component_name: str, row: dict):
    key = component_name + "_".join([str(value) for key, value in row.items()])
    if st.button("Undeploy", key=key, type="primary"):
        model_name = row["Name"]
        version = row.get("version", "latest")
        status = undeploy_model(project_name=project_name, model_name=model_name, version=version)
        st.session_state["action_model_undeploy_ok"] = status
        st.rerun()


def build_get_button(project_name: str, component_name: str, row: dict):
    key = component_name + "_".join([str(value) for key, value in row.items()])
    if st.button("Get", key=key, type="primary"):
        model_name = row["Name"]
        status = get_model(project_name=project_name, model_name=model_name)
        st.session_state["action_get_ok"] = status
        st.rerun()


def build_dashboard_button(row: dict):
    url = row.get("dashboard_url", "#")
    st.link_button("📊", url=url, help="Open Grafana Dashboard")
