import json
import os

import httpx
import typer

from cli.endpoints import API_URL

TOKEN_FILE = os.path.expanduser("~/.mycli_token.json")


def save_token(token: dict):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f)


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

def get_client() -> httpx.Client:
    token = load_token()
    if not token:
        typer.echo("You need to login first (use `mycli login`).")
        raise typer.Exit(1)
    return httpx.Client(
        base_url=API_URL,
        headers={"Authorization": f"Bearer {token['access_token']}"},
        verify=False
    )