import pandas as pd
import streamlit as st

from front.api_interactions.endpoints import (
    ADD_USER_TO_PROJECT,
    CHANGE_USER_ROLE_FOR_PROJECT,
    CREATE_USER_URI,
    DELETE_USER_FOR_PROJECT,
    GET_ALL_USERS_URI,
    GET_USERS_FOR_PROJECT,
)
from front.api_interactions.projects import format_users_list
from front.utils import send_get_query, send_post_query

ROLE_OPTIONS = ["VIEWER", "DEVELOPER", "MAINTAINER", "ADMIN"]


def get_all_users() -> pd.DataFrame:
    url = GET_ALL_USERS_URI
    result = send_get_query(url)
    users_list = result["data"]["users"]
    if result["http_code"] != 200:
        st.toast("Error while fetching users")
        return pd.DataFrame()
    return users_list


def add_user_to_project_with_role(user, role, project_name):
    url = ADD_USER_TO_PROJECT.format(email=user, role=role, project_name=project_name)
    result = send_post_query(url, json_data={})
    if result["http_code"] != 200:
        st.session_state["added_user_to_project_success"] = False
    else:
        st.session_state["added_user_to_project_success"] = result
    return result


def change_user_role_for_project(email, role, project_name):
    url = CHANGE_USER_ROLE_FOR_PROJECT.format(email=email, role=role, project_name=project_name)
    result = send_post_query(url, json_data={})
    if result["http_code"] != 200:
        st.session_state["change_user_role_for_project_success"] = False
    else:
        st.session_state["change_user_role_for_project_success"] = True
    return result


def create_user(email: str, password: str):
    url = CREATE_USER_URI.format(email=email, password=password)
    result = send_post_query(url, json_data={})
    print(result)
    if result["http_code"] != 200:
        st.toast(result["data"]["detail"], icon="❌")
        return False
    else:
        st.toast(result["data"]["detail"], icon="✅")
        return True


def get_users_for_project(project_name: str) -> pd.DataFrame:
    url = GET_USERS_FOR_PROJECT.format(project_name=project_name)
    result = send_get_query(url)
    if result["http_code"] != 200:
        st.toast(result["data"]["detail"], icon="❌")
        return pd.DataFrame()
    else:
        project_users = result["data"]["users"]
        return format_users_list(project_users)


def remove_user_from_project(email: str, project_name: str):
    st.session_state["removed_user_from_project_success"] = True
    url = DELETE_USER_FOR_PROJECT.format(email=email, project_name=project_name)
    send_post_query(url, json_data={})
    return True
