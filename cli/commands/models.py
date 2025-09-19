from cli.utils.api_calls import get_and_print


def list_models(project_name: str):
    """List existing models for a project"""
    get_and_print(f"/{project_name}/models/list", "❌ Error retrieving models", success_message="✅ Models retrieved successfully")

def deploy_model(project_name: str, model_name: str, model_version: str):
    """Deploy a new model to a project"""
    get_and_print(f"/{project_name}/models/deploy/{model_name}/{model_version}",
                  "❌ Error deploying model", success_message="✅ Model deployed successfully")

#/test/models/deploy/test_model/1