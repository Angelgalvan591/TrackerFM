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
