import requests

BASE = "https://api.deezer.com"


def buscar_deezer(query, tipo="track", limite=20):
    try:
        endpoint = f"/search/{tipo}" if tipo in ["artist", "album"] else "/search"
        r = requests.get(f"{BASE}{endpoint}", params={"q": query, "limit": limite}, timeout=6)
        return r.json().get("data", [])
    except Exception:
        return []

def get_album_details(album_id):
    try:
        r = requests.get(f"{BASE}/album/{album_id}")
        return r.json()
    except Exception:
        return {}

def get_artist_details(artist_id):
    try:
        r = requests.get(f"{BASE}/artist/{artist_id}")
        return r.json()
    except Exception:
        return {}

def get_artist_albums(artist_id, limite=20):
    try:
        r = requests.get(f"{BASE}/artist/{artist_id}/albums", params={"limit": limite})
        return r.json().get("data", [])
    except Exception:
        return []

def get_artist_top_tracks(artist_id, limite=10):
    try:
        r = requests.get(f"{BASE}/artist/{artist_id}/top", params={"limit": limite})
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
