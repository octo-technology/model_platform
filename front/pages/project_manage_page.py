import streamlit as st

from front.st_creators.project_manage_page_items import create_project_list

st.title("Project Management")
st.write("### Project list")

create_project_list()
