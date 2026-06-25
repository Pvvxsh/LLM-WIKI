def sort(data):
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if "choices" not in data or not data["choices"]:
        return ""
    return data["choices"][0]["message"]["content"]
