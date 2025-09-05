import typer

from cli.commands.auth import login, me
from cli.commands.projects import list_projects, add_project, delete_project

app = typer.Typer()
project_app = typer.Typer()
app.add_typer(project_app, name="projects")

app.command()(login)
app.command()(me)

project_app.command("list")(list_projects)
project_app.command("add")(add_project)
project_app.command("delete")(delete_project)
if __name__ == "__main__":
    app()
