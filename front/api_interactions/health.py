import requests

from front.utils import send_get_query

STATUS_COLOR = {"healthy": "🟢", "unhealthy": "🟠", "unreachable": "🔴"}


def check_url_health(url):
    try:
        response = send_get_query(url)
        if response["http_code"] == 200:
            return "healthy", STATUS_COLOR["healthy"]
        else:
            return "unhealthy", STATUS_COLOR["unhealthy"]
    except requests.RequestException:
        return "unreachable", STATUS_COLOR["unreachable"]
