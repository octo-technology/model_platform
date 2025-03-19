from front.utils import send_get_query

STATUS_COLOR = {"healthy": "🟢", "unhealthy": "🟠", "unreachable": "🔴"}


def check_url_health(url):
    response = send_get_query(url)
    if response["http_code"] in [200, 403]:
        return "healthy", STATUS_COLOR["healthy"]
    else:
        return "unhealthy", STATUS_COLOR["unhealthy"]
