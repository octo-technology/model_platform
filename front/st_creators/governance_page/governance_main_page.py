import json
from collections import defaultdict

import pandas as pd
import streamlit as st

from front.api_interactions.governance import get_project_full_governance
from front.api_interactions.projects import get_projects_list


def create_governance_main_page():
    st.markdown("# Model Governance")
    st.write("")
    st.write("")
    with st.container():
        cols = st.columns(2)
        with cols[0]:
            create_project_selection_list()
        with cols[1]:
            create_project_governance_download("test")
    st.divider()
    create_project_governance_frame("test")


def create_project_governance_download(project_name: str):
    with st.container(border=True):
        st.markdown("#### Download all information and artifacts for this project")
        # download_project_governance(project_name)
        if st.download_button("Download", data="", type="primary"):
            pass


def create_project_selection_list():
    projects_list_df = get_projects_list()
    projects_name_list = projects_list_df["Name"].tolist()
    with st.container(border=True):
        st.markdown("#### Please select a project to analyse:")
        st.selectbox(
            label="Select User",
            options=projects_name_list,
            key="governance_project_selection",
            label_visibility="collapsed",
        )


def create_project_governance_frame(project_name: str):
    json_data = get_project_full_governance(project_name)["data"]
    print(json_data)
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    if "project_gouvernance" not in data:
        st.error("Invalid JSON format: 'project_gouvernance' key not found")
        return
    st.markdown("## Registered Models")

    st.write(
        "You will find the list of all the models of your project, including their description (model card) "
        "as well as their versions and deployment events."
    )
    st.write(" ")

    model_groups = defaultdict(list)
    for model_data in data["project_gouvernance"]:
        if "model_information" not in model_data:
            continue

        model_info = model_data["model_information"]
        if "model_name" not in model_info:
            continue

        model_name = model_info["model_name"]
        model_groups[model_name].append(model_data)

    for model_name, model_versions in model_groups.items():
        with st.container(border=False):
            st.markdown("## Model overview")
            cols = st.columns([0.01, 0.99])
            cols[1].markdown(f"#### Model name : {model_name}")

            versions_data = []
            all_events = []

            for model_data in model_versions:
                model_info = model_data["model_information"]

                version_info = {
                    "Version": model_info.get("version", "Unknown"),
                    "Run ID": model_info.get("run_id", "Unknown"),
                    "Run Name": model_info.get("tags", {}).get("mlflow.runName", "Unnamed Run"),
                    "User": model_info.get("tags", {}).get("mlflow.user", "Unknown"),
                    "Accuracy": model_info.get("metrics", {}).get("accuracy", "N/A"),
                    "Created Date": extract_creation_date(model_info),
                }
                versions_data.append(version_info)

                if "events" in model_data and model_data["events"]:
                    for event in model_data["events"]:
                        if event.get("deployment_date", "").startswith("1970-01-01"):
                            continue

                        event_info = event.copy()
                        event_info["version"] = model_info.get("version", "Unknown")
                        all_events.append(event_info)

            if (
                model_versions
                and "model_information" in model_versions[0]
                and "tags" in model_versions[0]["model_information"]
            ):
                latest_version = max(model_versions, key=lambda x: x["model_information"].get("version", "0"))
                if "mlflow.note.content" in latest_version["model_information"]["tags"]:
                    description = latest_version["model_information"]["tags"]["mlflow.note.content"]
                    cols_card = st.columns([0.01, 0.99])
                    with cols_card[1]:
                        st.markdown("#### Model card:")
                        st.text_area("", description, height=300, label_visibility="collapsed")

            st.markdown("#### Model Versions")
            if versions_data:
                versions_df = pd.DataFrame(versions_data)
                if "Version" in versions_df.columns:
                    versions_df["Version"] = pd.to_numeric(versions_df["Version"])
                    versions_df = versions_df.sort_values("Version", ascending=False)
                st.dataframe(versions_df, use_container_width=True)
            else:
                st.info("No version information available")

            st.markdown("#### Deployment Events")
            if all_events:
                events_df = pd.DataFrame(all_events)

                if "deployment_date" in events_df.columns:
                    events_df["deployment_date"] = pd.to_datetime(events_df["deployment_date"])
                    events_df["deployment_date"] = events_df["deployment_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

                if "deployment_date" in events_df.columns:
                    events_df = events_df.sort_values("deployment_date", ascending=False)

                events_df = events_df.rename(
                    columns={
                        "deployment_date": "Deployment Date",
                        "deployment_name": "Deployment Name",
                        "version": "Version",
                        "project_name": "Project Name",
                        "model_name": "Model Name",
                    }
                )

                st.dataframe(events_df, use_container_width=True)
            else:
                st.info("No deployment events found for this model")

        st.divider()
        st.write(" ")


def extract_creation_date(model_info):
    """Extract creation date from model_info if available"""
    if "tags" in model_info and "mlflow.log-model.history" in model_info["tags"]:
        history = json.loads(model_info["tags"]["mlflow.log-model.history"])
        if isinstance(history, list) and len(history) > 0:
            return history[0].get("utc_time_created", "Unknown")

    return "Unknown"
