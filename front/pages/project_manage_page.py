import streamlit as st

from front.api_interactions.projects import get_projects_list

st.title("Project Management")
st.write("### Project list")

projects_df = get_projects_list()
