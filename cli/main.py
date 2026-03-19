import typer

from cli.commands.auth import login, me
from cli.commands.batch import batch_status, delete_batch_job, download_batch_result, list_batch_jobs, submit_batch
from cli.commands.demo import get_status, list_simulations, start_simulation, stop_simulation
from cli.commands.models import deploy_model, list_deployed_models, list_models, search_model_infos, undeploy_model
from cli.commands.projects import (
    add_project,
    add_user_to_project,
    delete_project,
    disable_batch,
    enable_batch,
    list_projects,
    project_info,
)
from cli.commands.users import add_user, list_users

app = typer.Typer()
project_app = typer.Typer()
user_app = typer.Typer()
demo_app = typer.Typer()
batch_app = typer.Typer()
app.add_typer(project_app, name="projects")
app.add_typer(user_app, name="users")
app.add_typer(demo_app, name="demo")
app.add_typer(batch_app, name="batch")

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
project_app.command("enable-batch")(enable_batch)
project_app.command("disable-batch")(disable_batch)
user_app.command("list")(list_users)
user_app.command("add")(add_user)
demo_app.command("list")(list_simulations)
demo_app.command("start")(start_simulation)
demo_app.command("stop")(stop_simulation)
demo_app.command("status")(get_status)
batch_app.command("submit")(submit_batch)
batch_app.command("status")(batch_status)
batch_app.command("list")(list_batch_jobs)
batch_app.command("download")(download_batch_result)
batch_app.command("delete")(delete_batch_job)
if __name__ == "__main__":
    app()
