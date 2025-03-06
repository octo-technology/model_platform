from front.utils import send_get_query

STATUS_COLOR = {"healthy": "🟢", "unhealthy": "🟠", "unreachable": "🔴"}


def check_url_health(url):
    response = send_get_query(url)
    if response["http_code"] == 200:
        print(url, response)
        return "healthy", STATUS_COLOR["healthy"]
    else:
        return "unhealthy", STATUS_COLOR["unhealthy"]
