import streamlit as st

from frontend.api_interactions.projects import add_project, delete_project
from frontend.st_creators.project_page.demo_projects import get_random_demo_project


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
                st.button("Add project", type="primary", on_click=set_add_project_button_state)
    if st.session_state.get("add_project_button", False):
        create_project_creation_container()
    else:
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
                                col_obj.button(label, type="tertiary", key=f"clicked_project_{col_name}_{row['Name']}")
                            else:
                                col_obj.write(label)
                    if show_delete_button:
                        with col_objects[-1]:
                            build_project_deletion_bin(row["Name"])


def build_project_deletion_bin(project_name: str):
    st.session_state["show_delete_dialog"] = None
    st.button(
        label="",
        icon="🗑️",
        type="tertiary",
        key=f"delete_project_{project_name}",
        use_container_width=True,
        on_click=create_st_dialog_delete_project,
        args=[project_name],
    )


def set_bool_display_delete_dialog(value: bool):
    st.session_state["display_delete_dialog"] = value


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


def set_add_project_button_state():
    if st.session_state.get("add_project_button", False):
        st.session_state["add_project_button"] = False
    else:
        st.session_state["add_project_button"] = True


def create_project_creation_container():
    # Auto-fill demo button outside the form
    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
    with col3:
        if st.button("🎲 Auto-fill démo", help="Remplir automatiquement avec un projet d'exemple", use_container_width=True):
            demo_project = get_random_demo_project()
            st.session_state["demo_project_name"] = demo_project["name"]
            st.session_state["demo_project_owner"] = demo_project["owner"]
            st.session_state["demo_project_scope"] = demo_project["scope"]
            st.session_state["demo_project_data_perimeter"] = demo_project["data_perimeter"]
            st.rerun()

    with st.form("Project Creation"):
        name = st.text_input(
            "Name",
            placeholder="Insert a project name",
            value=st.session_state.get("demo_project_name", "")
        )
        owner = st.text_input(
            "Owner",
            placeholder="Insert a project owner (person or organization), responsible for this project.",
            value=st.session_state.get("demo_project_owner", "")
        )
        scope = st.text_area(
            "Scope",
            placeholder="Insert a project scope: what is this project about?",
            value=st.session_state.get("demo_project_scope", ""),
            height=150
        )
        data_perimeter = st.text_area(
            "Data perimeter",
            placeholder="Insert a description about the data perimeter of this project.",
            value=st.session_state.get("demo_project_data_perimeter", ""),
            height=150
        )
        submitted = st.form_submit_button("Create Project")
        if submitted:
            add_project(name, owner, scope, data_perimeter)
            st.session_state["add_project_button"] = False
            # Clear demo data after submission
            for key in ["demo_project_name", "demo_project_owner", "demo_project_scope", "demo_project_data_perimeter"]:
                if key in st.session_state:
                    del st.session_state[key]
