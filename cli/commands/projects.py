from cli.utils.output import pretty_print
from cli.utils.token import get_client


def list_projects():
    """Get current user info"""
    client = get_client()
    r = client.get("/projects/list")
    if r.status_code == 200:
        projects = r.json()
        if not projects:
            print("[yellow]Aucun projet trouvé.[/yellow]")
            return
        pretty_print(projects)
    else:
        print("[red]❌ Error fetching projects[/red]")


def add_project(name: str, owner: str = "", scope: str = "", data_perimeter: str = ""):
    """Create a new project"""
    client = get_client()
    r = client.post("/projects/add", json={
        "name": name,
        "owner": owner,
        "scope": scope,
        "data_perimeter": data_perimeter
    })
    if r.status_code == 200:
        print("[green]✅ Project created successfully[/green]")
        print(r.json())
    else:
        print(r.content)
        print("[red]❌ Error creating project[/red]")

def delete_project(name: str):
    """Delete a project by ID"""
    client = get_client()
    r = client.get(f"/projects/{name}/remove")
    if r.status_code == 200:
        print("[green]✅ Project deleted successfully[/green]")
    else:
        print(r.content)
        print("[red]❌ Error deleting project[/red]")