from cli.utils.api_calls import get_and_print


def list_models(project_name: str):
    """List existing models for a project"""
    get_and_print(f"/{project_name}/models/list", "❌ Error retrieving models", success_message="✅ Models retrieved successfully")