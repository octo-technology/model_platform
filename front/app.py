import streamlit as st

from front.api_interactions.endpoints import HEALTH_ENDPOINT
from front.api_interactions.health import check_backend_health

pg = st.navigation(
    [
        st.Page("pages/project_page.py", title="🤖 Project page"),
        st.Page("pages/project_manage_page.py", title="⚙️ Manage project"),
    ]
)

pg.run()

# Affichage de l'état avec une pastille
st.sidebar.title("Backend status")

status_colors = {"healthy": "🟢", "unhealthy": "🟠", "unreachable": "🔴"}
status = check_backend_health(HEALTH_ENDPOINT)
st.sidebar.markdown(f"{status_colors[status]} {status.capitalize()}")
