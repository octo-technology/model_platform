import typer

from cli.commands.auth import login, me
from cli.commands.models import list_models, deploy_model, undeploy_model, list_deployed_models
from cli.commands.projects import list_projects, add_project, delete_project, project_info, add_user_to_project
from cli.commands.users import list_users, add_user

app = typer.Typer()
project_app = typer.Typer()
user_app = typer.Typer()
app.add_typer(project_app, name="projects")
app.add_typer(user_app, name="users")

app.command()(login)
app.command()(me)

project_app.command("list")(list_projects)
project_app.command("info")(project_info)
project_app.command("add")(add_project)
project_app.command("add-user")(add_user_to_project)
project_app.command("list-models")(list_models)
project_app.command("deploy")(deploy_model)
project_app.command("undeploy")(undeploy_model)
project_app.command("list-deployed-models")(list_deployed_models)
project_app.command("delete")(delete_project)
user_app.command("list")(list_users)
user_app.command("add")(add_user)
if __name__ == "__main__":
    app()
