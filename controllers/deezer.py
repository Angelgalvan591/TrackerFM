import requests


def buscar_deezer(query, limite=10):
    try:
        r = requests.get("https://api.deezer.com/search", params={"q": query, "limit": limite})
        return r.json().get("data", [])
    except Exception:
        return []
