import streamlit as st

from frontend.api_interactions.deployed_models import get_deployed_models_list
from frontend.api_interactions.endpoints import DEPLOYED_MODELS_LIST_ENDPOINT, MODELS_LIST_ENDPOINT
from frontend.api_interactions.governance import get_governance_per_model
from frontend.api_interactions.models import get_models_list
from frontend.api_interactions.projects import get_projects_list
from frontend.st_creators.model_versions_tab import model_versions_tab
from frontend.st_creators.project_page.project_model_listing import build_model_version_listing

if "tabs" not in st.session_state:
    st.session_state["tabs"] = ["Project's models", "Governance"]
tabs = st.tabs(st.session_state["tabs"])

with tabs[0]:
    if "selected_project" in st.session_state:
        st.title("PROJECT : '" + st.session_state["selected_project"] + "'")
    project_list = get_projects_list()
    if "selected_project" in st.session_state:
        project_name = st.session_state["selected_project"]
        models = get_models_list(MODELS_LIST_ENDPOINT, project_name)
        deployed_models = get_deployed_models_list(DEPLOYED_MODELS_LIST_ENDPOINT.format(project_name=project_name))
        st.write("#### Available models")
        build_model_version_listing(models, elements_to_add=["List versions", "Deploy latest"])
        st.write("#### Deployed models")
        build_model_version_listing(deployed_models, elements_to_add=["Undeploy"])

if "list_versions" in st.session_state:
    with tabs[-1]:
        model_versions_tab()

with tabs[1]:
    if "selected_project" in st.session_state:
        model_gov = get_governance_per_model(st.session_state["selected_project"])
        for model in model_gov:
            st.table(model)
