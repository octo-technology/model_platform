import pandas as pd
import streamlit as st

from front.api_interactions import endpoints
from front.api_interactions.deployed_models import get_build_status
from front.api_interactions.models import deploy_model
from front.api_interactions.projects import get_users_for_project
from front.api_interactions.users import (
    ROLE_OPTIONS,
    add_user_to_project_with_role,
    change_user_role_for_project,
    get_all_users,
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


def build_status(row: dict):
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
        st.session_state["tabs"] = ["Project's models", "Governance", row["Name"] + " versions"]
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


def create_projects_listing(projects_list_df, show_delete_button: bool = True, show_edit_buttons=True):
    cols = st.columns([0.7, 0.3])
    with cols[0]:
        st.write("")
    if show_edit_buttons:
        with cols[1]:
            cols_1 = st.columns([0.3, 0.3, 0.3], gap="small")
            with cols_1[1]:
                st.button("Edit Project")
            with cols_1[2]:
                st.button("Add project", type="primary")
    with st.container():
        if projects_list_df is not None and not projects_list_df.empty:
            if show_delete_button:
                columns = list(projects_list_df.columns) + ["Delete project"]
            else:
                columns = list(projects_list_df.columns)
            col_sizes = [2] * (len(columns))
            col_objects = st.columns(col_sizes)
            for col_obj, col_name in zip(col_objects, columns):
                col_obj.write(f"**{col_name}**")
            for _, row in projects_list_df.iterrows():
                col_objects = st.columns(col_sizes)
                for col_obj, col_name in zip(col_objects, columns):
                    if col_name in projects_list_df.columns:
                        if col_name in ["Name"]:
                            label = f" :blue[{row[col_name]}]"
                        else:
                            label = f" {row[col_name]}"
                        if col_name not in "Registry homepage":
                            col_obj.button(label, type="tertiary", key=f"clicked_project_{col_name}_{row[col_name]}")
                        else:
                            col_obj.write(label)
                if show_delete_button:
                    with col_objects[-1]:
                        build_project_deletion_bin(row["Name"])


def create_project_settings(projects_list_df: pd.DataFrame, project_name: str):
    project_settings, available_models, deployed_models = st.tabs(
        ["Project settings", "Available Models", "Deployed Models"]
    )
    with project_settings:
        st.markdown("### Project information")
        create_projects_listing(
            projects_list_df[projects_list_df["Name"] == project_name],
            show_delete_button=False,
            show_edit_buttons=False,
        )
        create_users_listing(project_name)
    with available_models:
        st.write("")
    with deployed_models:
        st.write("")


def set_bool_display_delete_dialog(value: bool):
    st.session_state["display_delete_dialog"] = value


def build_project_deletion_bin(project_name: str):
    st.session_state["show_delete_dialog"] = None
    st.button(
        label="",
        icon="🗑️",
        type="tertiary",
        key=f"delete_project_{project_name}",
        use_container_width=True,
        on_click=set_bool_display_delete_dialog,
        args=[True],
    )

    if st.session_state.get("display_delete_dialog", False):
        create_st_dialog_delete_project(project_name)


@st.dialog("Project Deletion Confirmation")
def create_st_dialog_delete_project(project_name: str):
    st.write(f"Are you sure you want to delete the project **{project_name}**?")
    st.session_state["current_page_to_display"] = "Projects"
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, delete", key=f"confirm_delete_{project_name}"):
            delete_project(project_name)
            st.session_state["display_delete_dialog"] = False
            st.rerun()

    with col2:
        if st.button("Cancel", key=f"cancel_delete_{project_name}"):
            st.session_state["display_delete_dialog"] = False
            st.rerun()


def delete_project(project_name: str):
    st.session_state["display_delete_project_success"] = project_name


def create_delete_project_success(project_name: str):
    st.toast(f"Delete project {project_name} successfully", icon="✅")
    st.session_state["display_delete_project_success"] = False


def create_add_user_success():
    st.toast("User successfully added", icon="✅")
    st.session_state["added_user_to_project_success"] = False


def create_changed_user_role_success():
    st.toast("User role successfully changed", icon="✅")
    st.session_state["changed_user_role_project_success"] = False


def create_users_listing(project_name: str):
    st.write("")
    st.markdown("### Users access")
    cols = st.columns([0.7, 0.3])
    with cols[0]:
        st.write("")
    with cols[1]:
        cols_1 = st.columns([0.3, 0.3, 0.3], gap="small")
        with cols_1[1]:
            st.button("Edit Users", key="edit_users")
        with cols_1[2]:
            st.button("Add User", type="primary", key="add_user")
    if st.session_state["add_user"]:
        display_line_add_user = True
    else:
        display_line_add_user = False
    if st.session_state["edit_users"]:
        edit_users = True
    else:
        edit_users = False
    with st.container():
        df_users_role = get_users_for_project(project_name)
        if df_users_role is not None and not df_users_role.empty:
            columns = list(df_users_role.columns)
            col_sizes = [2] * (len(columns))
            col_objects = st.columns(col_sizes)
            for col_obj, col_name in zip(col_objects, columns):
                col_obj.write(f"**{col_name}**")
            for _, row in df_users_role.iterrows():
                col_objects = st.columns(col_sizes)
                for col_obj, col_name in zip(col_objects, columns):
                    if col_name in df_users_role.columns:
                        if col_name in ["Role"] and edit_users:
                            col_obj.selectbox(
                                label="",
                                options=ROLE_OPTIONS,
                                index=ROLE_OPTIONS.index(row["Role"]),
                                key="selected_user_role_" + row["Name"],
                                on_change=change_user_role_for_project,
                            )
                        else:
                            col_obj.write(row[col_name])
            if display_line_add_user:
                col_objects = st.columns(col_sizes + [2])
                col_objects[0].selectbox(label="", options=get_all_users(), key="selected_add_user")
                col_objects[1].selectbox(label="", options=ROLE_OPTIONS, key="selected_role_user")
                col_objects[2].button(
                    "➕", type="tertiary", key="add_user_confirmation_button", on_click=add_user_to_project_with_role
                )
