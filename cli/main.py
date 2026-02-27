import typer

from cli.commands.auth import login, me
from cli.commands.models import deploy_model, list_deployed_models, list_models, search_model_infos, undeploy_model
from cli.commands.projects import add_project, add_user_to_project, delete_project, list_projects, project_info
from cli.commands.users import add_user, list_users

app = typer.Typer()
project_app = typer.Typer()
user_app = typer.Typer()
app.add_typer(project_app, name="projects")
app.add_typer(user_app, name="users")

app.command()(login)
app.command()(me)
app.command()(search_model_infos)

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
