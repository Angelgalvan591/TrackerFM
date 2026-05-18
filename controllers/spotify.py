import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

_sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id="54b436370c824a7598626d32ac95258d",
    client_secret="44c6e175ec5343faad87016220022b99",
))

def buscar(query, tipo="track", limite=10):
    try:
        res = _sp.search(q=query, type=tipo, limit=limite)
        if tipo == "track":
            return res["tracks"]["items"]
        if tipo == "album":
            return res["albums"]["items"]
        if tipo == "artist":
            return res["artists"]["items"]
    except Exception:
        return []


def get_artist_top_tracks(artist_id, market="US"):
    try:
        res = _sp.artist_top_tracks(artist_id, country=market)
        return res.get("tracks", [])[:10]
    except Exception:
        return []


def get_artist_albums(artist_id, limite=20):
    try:
        res = _sp.artist_albums(artist_id, album_type="album,single", limit=limite)
        return res.get("items", [])
    except Exception:
        return []


def get_artist_full(artist_id):
    try:
        return _sp.artist(artist_id)
    except Exception:
        return None


def get_album_tracks(album_id):
    try:
        res = _sp.album_tracks(album_id, limit=50)
        album = _sp.album(album_id)
        tracks = res.get("items", [])
        # inyectar imagen del album en cada track
        img = (album.get("images") or [{}])[0].get("url", "")
        for t in tracks:
            t["_album_img"] = img
            t["_album_name"] = album.get("name", "")
        return tracks, album
    except Exception:
        return [], {}
