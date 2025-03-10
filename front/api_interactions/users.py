import streamlit as st

ROLE_OPTIONS = ["Viewer", "Developer", "Maintainer", "Admin"]


def get_all_users() -> list:
    return ["stil@example.com", "toul@example.com", "lich@example.com"]


def add_user_to_project_with_role():

    st.session_state["added_user_to_project_success"] = True
    return True


def change_user_role_for_project():
    st.session_state["changed_user_role_project_success"] = True
    return True
