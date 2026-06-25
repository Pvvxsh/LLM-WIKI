def get_tokens(data):
    if isinstance(data, str):
        return len(data)
    try:
        return data.get("usage", {}).get("total_tokens", 0)
    except:
        return 0
