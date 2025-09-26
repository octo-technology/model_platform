import typer

from cli.utils.api_calls import get_and_print


def list_models(project_name: str):
    """List existing models for a project"""
    get_and_print(f"/{project_name}/models/list", "❌ Error retrieving models", success_message="✅ Models retrieved successfully")

def deploy_model(project_name: str, model_name: str = typer.Option(), model_version: str= typer.Option()):
    """Deploy a new model to a project"""
    get_and_print(f"/{project_name}/models/deploy/{model_name}/{model_version}",
                  "❌ Error deploying model", success_message="✅ Model deployed successfully")

def undeploy_model(project_name: str, model_name: str = typer.Option(), model_version: str= typer.Option()):
    """Undeploy a model from a project"""
    get_and_print(f"/{project_name}/models/undeploy/{model_name}/{model_version}",
                  "❌ Error undeploying model", success_message="✅ Model undeployed successfully")

def list_deployed_models(project_name: str):
    """List deployed models for a project"""
    get_and_print(f"/{project_name}/deployed_models/list", "❌ Error retrieving deployed models", success_message="✅ Deployed models retrieved successfully")