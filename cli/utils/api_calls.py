from cli.utils.token import get_client


def pretty_print(output_json):
    try:
        headers = list(output_json[0].keys())
    except KeyError:
        headers = list(output_json.keys())
    print(" ".join(f"{h:20}" for h in headers))
    print("-" * (len(headers) * 21))
    if isinstance(output_json, list):
        for p in output_json:
            print(" ".join(f"{str(p.get(h, '')):20}" for h in headers))
    else:
        print(" ".join(f"{str(output_json.get(h, '')):20}" for h in headers))


def get_and_print(endpoint: str, error_message: str = "❌ Error fetching query",
                  success_message: str = "Empty") -> None:
    client = get_client()
    r = client.get(endpoint)
    print(r.content)
    if r.status_code == 200:
        projects = r.json()
        if not projects:
            print(success_message)
            return
        pretty_print(projects)
    else:
        print(error_message)


def post_and_print(endpoint: str, payload: dict, error_message: str = "❌ Error",
                   success_message: str = "✅Success") -> None:
    client = get_client()
    if payload is not None:
        r = client.post(endpoint, json=payload)
    else:
        r = client.post(endpoint)
    if r.status_code == 200:
        print(success_message)
    else:
        print(r.content)
        print(error_message)
