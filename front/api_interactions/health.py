import requests


def check_backend_health(url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return "healthy"
        else:
            return "unhealthy"
    except requests.RequestException:
        return "unreachable"
