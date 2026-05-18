import requests

BASE = "https://api.deezer.com"


def buscar_deezer(query, limite=10):
    try:
        r = requests.get(f"{BASE}/search", params={"q": query, "limit": limite})
        return r.json().get("data", [])
    except Exception:
        return []


def get_chart_tracks(limite=10):
    try:
        r = requests.get(f"{BASE}/chart/0/tracks", params={"limit": limite})
        return r.json().get("data", [])
    except Exception:
        return []


def get_chart_albums(limite=10):
    try:
        r = requests.get(f"{BASE}/chart/0/albums", params={"limit": limite})
        return r.json().get("data", [])
    except Exception:
        return []


def get_chart_artists(limite=10):
    try:
        r = requests.get(f"{BASE}/chart/0/artists", params={"limit": limite})
        return r.json().get("data", [])
    except Exception:
        return []


def get_preview(track_name, artist_name):
    try:
        q = f"{track_name} {artist_name}"
        r = requests.get(f"{BASE}/search", params={"q": q, "limit": 1})
        data = r.json().get("data", [])
        return data[0].get("preview", "") if data else ""
    except Exception:
        return ""
