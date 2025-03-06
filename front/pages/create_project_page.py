import streamlit as st

from front.api_interactions.projects import add_project

st.title("Create a project")

with st.form(key="create_project_form"):
    st.subheader("Create a New Project")

    project_name = st.text_input("Project Name")
    project_owner = st.text_input("Project Owner")
    project_scope = st.text_area("Project scope")
    project_data_perimeter = st.text_area("Project data perimeter")

    submit_button = st.form_submit_button("Create Project")
    if submit_button:
        if project_name and project_scope and project_owner and project_data_perimeter:
            success = add_project(
                name=project_name, owner=project_owner, scope=project_scope, data_perimeter=project_data_perimeter
            )
        else:
            st.error("Please fill in all the fields.")
