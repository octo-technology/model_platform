import requests

STATUS_COLOR = {"healthy": "🟢", "unhealthy": "🟠", "unreachable": "🔴"}


def check_url_health(url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return "healthy", STATUS_COLOR["healthy"]
        else:
            return "unhealthy", STATUS_COLOR["unhealthy"]
    except requests.RequestException:
        return "unreachable", STATUS_COLOR["unreachable"]
