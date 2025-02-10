import streamlit
import streamlit as st

from front.api_interactions.deployed_models import get_deployed_models_list
from front.api_interactions.endpoints import DEPLOYED_MODELS_LIST_ENDPOINT, MODELS_LIST_ENDPOINT
from front.api_interactions.models import get_models_list
from front.api_interactions.projects import get_projects_list
from front.st_creators.project_page_items import (
    create_project_deployed_models_listing,
    create_project_model_listing,
    create_project_selection_sidebar,
)

if "selected_project" in st.session_state:
    st.title("PROJECT : '" + st.session_state["selected_project"] + "'")
project_list = get_projects_list()
if "selected_project" in st.session_state:
    project_name = st.session_state["selected_project"]
    models = get_models_list(MODELS_LIST_ENDPOINT, project_name)
    deployed_models = get_deployed_models_list(DEPLOYED_MODELS_LIST_ENDPOINT)
    create_project_model_listing(models)
    create_project_deployed_models_listing(deployed_models)

create_project_selection_sidebar(project_list)
