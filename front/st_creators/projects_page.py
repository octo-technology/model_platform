import streamlit as st

from front.api_interactions.projects import create_projects_listing, display_delete_project_success


def create_projects_page():
    st.title("Projects")
    st.write("")
    cols = st.columns([0.7, 0.3])
    st.write("")
    with cols[0]:
        st.write("")
    with cols[1]:
        cols_1 = st.columns([0.3, 0.3, 0.3], gap="small")
        with cols_1[1]:
            st.button("Edit Project")
        with cols_1[2]:
            st.button("Add project", type="primary")

    with st.container():
        create_projects_listing()

    if st.session_state.get("display_delete_project_success", False):
        display_delete_project_success(st.session_state["display_delete_project_success"])
