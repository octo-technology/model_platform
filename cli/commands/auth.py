import os

import httpx
import typer

from cli.endpoints import API_URL
from cli.utils.output import pretty_print
from cli.utils.token import save_token, get_client

TOKEN_FILE = os.path.expanduser("~/.mycli_token.json")


def login(username: str, password: str):
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
    client = get_client()
    r = client.get("/auth/me")
    if r.status_code == 200:
        pretty_print(r.json())
    else:
        print("[red]❌ Error fetching user info[/red]")

