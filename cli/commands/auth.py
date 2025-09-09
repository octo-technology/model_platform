import os

import httpx
import typer

from cli.endpoints import API_URL
from cli.utils.api_calls import pretty_print, get_and_print, post_and_print
from cli.utils.token import save_token, get_client

TOKEN_FILE = os.path.expanduser("~/.mycli_token.json")


def login(username: str=typer.Option(), password: str=typer.Option()) -> None:
    """Authenticate and store OAuth token"""
    r = httpx.post(f"{API_URL}/auth/token", verify=False, data={
        "username": username,
        "password": password
    })
    if r.status_code == 200:
        token = r.json()
        save_token(token)
        print("[green]✅ Logged in successfully[/green]")
    else:
        print("[red]❌ Login failed[/red]")
        raise typer.Exit(1)


def me():
    """Get current user info"""
    get_and_print("/auth/me")
