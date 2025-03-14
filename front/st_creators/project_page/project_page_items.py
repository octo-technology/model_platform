import pandas as pd
import streamlit as st

from front.api_interactions.deployed_models import get_deployed_models_list
from front.api_interactions.endpoints import MODELS_LIST_ENDPOINT
from front.api_interactions.models import get_models_list
from front.api_interactions.users import (
    ROLE_OPTIONS,
    add_user_to_project_with_role,
    change_user_role_for_project,
    get_all_users,
    get_users_for_project,
    remove_user_from_project,
)
from front.st_creators.project_page.project_listing import create_projects_listing
from front.st_creators.project_page.project_model_listing import build_model_version_listing


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
        models = get_models_list(MODELS_LIST_ENDPOINT, project_name)
        build_model_version_listing(models, project_name, elements_to_add=["Action"], component_name="available_models")
    with deployed_models:
        deployed_models_list = get_deployed_models_list(project_name)
        build_model_version_listing(
            deployed_models_list, project_name, elements_to_add=["Action"], component_name="deployed_models"
        )


def create_delete_project_success():
    project_name = st.session_state.get("display_delete_project_success", None)
    st.toast(f"Project {project_name} deleted successfully", icon="✅")
    st.session_state["display_delete_project_success"] = False


def create_add_user_success():
    st.toast("User successfully added", icon="✅")
    st.session_state["added_user_to_project_success"] = False


def create_changed_user_role_success():
    st.toast("User role successfully changed", icon="✅")
    st.session_state["change_user_role_for_project_success"] = False


def create_add_model_deployment_success():
    if st.session_state.get("action_model_deployment_ok", False):
        st.toast("Model successfully deployed", icon="✅")
        st.session_state["action_model_deployment_ok"] = False
    else:
        st.toast("Error while deploying model", icon="❌")


def create_add_model_undeploy_success():
    if st.session_state.get("action_model_undeploy_ok", False):
        st.toast("Model successfully deployed", icon="✅")
        st.session_state["action_model_undeploy_ok"] = False
    else:
        st.toast("Error while deploying model", icon="❌")


def create_users_listing(project_name: str):
    st.write("")
    st.markdown("### Users access")
    cols = st.columns([0.7, 0.3])
    with cols[0]:
        st.write("")
    with cols[1]:
        cols_1 = st.columns([0.3, 0.3, 0.3], gap="small")
        with cols_1[1]:
            if st.button("Edit Users", key="edit_users_button"):
                st.session_state["edit_users"] = not st.session_state.get("edit_users", False)
        with cols_1[2]:
            if st.button("Add User", type="primary", key="add_user_button"):
                st.session_state["add_user"] = not st.session_state.get("add_user", False)
                # Initialiser les valeurs par défaut lorsque le bouton est cliqué
                if "user_selection" not in st.session_state:
                    all_users = get_all_users()
                    st.session_state["user_selection"] = all_users[0] if all_users else None
                if "role_selection" not in st.session_state:
                    st.session_state["role_selection"] = ROLE_OPTIONS[0] if ROLE_OPTIONS else None

    display_line_add_user = st.session_state.get("add_user", False)
    edit_users = st.session_state.get("edit_users", False)
    create_user_edition_container(project_name, edit_users)
    create_user_addition_container(project_name, display_line_add_user)


def create_user_addition_container(project_name: str, display_line_add_user: bool):
    if display_line_add_user:
        form_key = "add_user_form"
        with st.form(key=form_key, border=False):
            add_user_cols = st.columns(3)
            all_users = get_all_users()
            add_user_cols[0].selectbox(
                label="Select User", options=all_users, key="form_user_selection", label_visibility="collapsed"
            )

            add_user_cols[1].selectbox(
                label="Select Role", options=ROLE_OPTIONS, key="form_role_selection", label_visibility="collapsed"
            )

            # Utiliser un bouton de soumission de formulaire
            submitted = add_user_cols[2].form_submit_button("➕")
            if submitted:
                user = st.session_state["form_user_selection"]
                role = st.session_state["form_role_selection"]
                add_user_to_project_with_role(user, role, project_name)
                st.success(f"User {user} added with role {role}")
                st.session_state["add_user"] = False
                st.rerun()


def create_user_edition_container(project_name: str, edit_users: bool):
    with st.container():
        df_users_role = get_users_for_project(project_name)
        if df_users_role is not None and not df_users_role.empty:
            columns = list(df_users_role.columns)
            col_sizes = [0.05] * (len(columns)) + [0.1]
            col_objects = st.columns(col_sizes)
            for col_obj, col_name in zip(col_objects, columns):
                col_obj.write(f"**{col_name}**")

            for _, row in df_users_role.iterrows():
                user_row_cols = st.columns(col_sizes)
                for i, col_name in enumerate(columns):
                    if col_name in df_users_role.columns:
                        if col_name == "Role" and edit_users:
                            role_key = f"role_{row['Name']}"
                            if role_key not in st.session_state:
                                st.session_state[role_key] = row["Role"]
                            user_row_cols[i].selectbox(
                                label="",
                                options=ROLE_OPTIONS,
                                index=ROLE_OPTIONS.index(st.session_state[role_key]),
                                key=role_key,
                                label_visibility="collapsed",
                            )
                        else:
                            user_row_cols[i].write(row[col_name])
                if edit_users:
                    with user_row_cols[-1]:
                        button_cols = st.columns([0.1, 0.1, 0.8])
                        if button_cols[0].button("🗑️", key=f"delete_user_{row['Name']}", type="secondary"):
                            remove_user_from_project(row["Name"], project_name)
                            st.rerun()
                        if button_cols[1].button("💾", key=f"save_role_{row['Name']}", type="secondary"):
                            change_user_role_for_project(row["Name"], st.session_state[role_key], project_name)
                            st.rerun()
