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
