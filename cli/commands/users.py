import typer

from cli.utils.api_calls import get_and_print, post_and_print


def list_users():
    """List existing users (Admin only)"""
    get_and_print("/users/get_all", "❌ Error retrieving users", success_message="✅ Users retrieved successfully")


def add_user(email: str = typer.Option(), password: str = typer.Option(), role: str = typer.Option):
    """Add a new user"""
    post_and_print(f"/users/add?email={email}&password={password}&role={role}", payload=None)


def delete_user(email: str):
    """delete an user by email"""
    # TODO
    pass
