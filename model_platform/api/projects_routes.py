from fastapi import APIRouter

router = APIRouter()

# Fix data to test front
PROJECT_NAMES = ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta"]
PROJECTS_INFOS = {
    project_name: {
        "name": project_name,
        "owner": project_name.split(" ")[-1] + " team",
        "scope": "A project to revolutionize IA projects",
        "data_perimeter": "All data on earth regarding our clients",
    }
    for project_name in PROJECT_NAMES
}


@router.get("/list")
def route_list_projects():
    return [e for e in PROJECTS_INFOS.values()]


@router.get("/{project_name}/info")
def rouge_project_info(project_name):
    return [e for k, e in PROJECTS_INFOS.items() if k == project_name]
