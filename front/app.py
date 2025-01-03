import streamlit as st

pg = st.navigation([
    st.Page("pages/project_page.py", title="🤖 Project page"),
    st.Page("pages/project_manage_page.py", title="⚙️ Manage project"),

])

pg.run()
