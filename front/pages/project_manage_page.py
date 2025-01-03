import streamlit as st


def show_create_project_popup():
    with st.form(key='create_project_form'):
        st.subheader("Create a New Project")

        project_name = st.text_input("Project Name")
        project_description = st.text_area("Project Description")
        project_owner = st.text_input("Project Owner")

        submit_button = st.form_submit_button("Create Project")

        if submit_button:
            if project_name and project_description and project_owner:
                st.success(f"Project '{project_name}' created successfully!")
            else:
                st.error("Please fill in all the fields.")


st.title("Project Management")
if st.button("Create New Project"):
    show_create_project_popup()
