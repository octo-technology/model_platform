import streamlit as st

from front.api_interactions.projects import get_projects_list

st.title("Project Management")
st.write("### Project list")

projects_df = get_projects_list()
if projects_df is None or projects_df.empty:
    st.warning("No projects found or the API is unreachable.")
    st.dataframe(projects_df)
