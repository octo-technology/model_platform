import typer

from cli.utils.api_calls import get_and_print, post_and_print
from cli.utils.token import get_client


def list_projects():
    """List existing projects"""
    get_and_print("/projects/list")


def project_info(name: str):
    """Get detailed info about a project by name"""
    get_and_print(f"/projects/{name}/info", error_message="❌ Error fetching project info",
                  success_message="✅ Project info retrieved successfully")


def add_project(name: str = typer.Option(), owner: str = typer.Option(""), scope: str = typer.Option(""),
                data_perimeter: str = typer.Option("")):
    """Create a new project"""
    post_and_print("/projects/add", {
        "name": name,
        "owner": owner,
        "scope": scope,
        "data_perimeter": data_perimeter
    }, error_message="❌ Error creating project", success_message="✅ Project created successfully")


def delete_project(name: str):
    """Delete a project by name"""
    get_and_print(f"/projects/{name}/remove", error_message="❌ Error deleting project",
                  success_message="✅ Project deleted successfully")


def add_user_to_project(project_name: str, email: str = typer.Option(), role: str = typer.Option()):
    """Add a user to a project with a specific role"""
    client = get_client()
    r = client.post(f"/projects/{project_name}/add_user?email={email}&role={role}")
    if r.status_code == 200:
        print("✅ User added to project successfully")
    else:
        print(r.content)
        print("❌ Error adding user to project")
