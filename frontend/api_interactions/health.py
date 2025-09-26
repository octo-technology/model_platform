from frontend.utils import send_get_query

STATUS_COLOR = {"healthy": "🟢", "unhealthy": "🟠", "unreachable": "🔴"}

def check_url_health(url):
    try:
        response = send_get_query(url, timeout=1)
        if response["http_code"] in [200, 403]:
            return "healthy", STATUS_COLOR["healthy"]
        else:
            return "unhealthy", STATUS_COLOR["unhealthy"]
    except Exception:
        return "unreachable", STATUS_COLOR["unreachable"]

