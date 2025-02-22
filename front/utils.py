import re

import requests


def sanitize_name(project_name: str) -> str:
    """Nettoie et format le nom pour être valid dans Kubernetes."""
    sanitized_name = re.sub(r"[^a-z0-9-]", "-", project_name.lower())
    sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Supprimer tirets au début
    sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Supprimer tirets à la fin
    return sanitized_name


def send_get_query(url: str) -> dict:
    """Envoie une requête GET à l'URL et retourne le contenu JSON."""
    response = requests.get(url)
    return {"http_code": response.status_code, "data": response.json() if response.ok else None}
