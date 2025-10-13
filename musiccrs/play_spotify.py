import os
from spotipy.oauth2 import SpotifyOAuth
import spotipy





# Récupérer les identifiants Spotify
client_id = CLIENT_ID = "6c5ce7f3ba45416ca6d5078ee52a6859"
client_secret = CLIENT_SECRET = "4e3727af29a344cfb89732c9a1abfbdf"
redirect_uri = SPOTIFY_REDIRECT_URI="http://127.0.0.1:8888/callback"

# Créer l'objet d'authentification
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="user-read-playback-state,user-modify-playback-state,streaming"
))

# Exemple : récupérer les infos sur un morceau
track_id = "spotify:track:7MmG8p0F9N3C4AXdK6o6Eb"  # Calvin Harris - Outside
track_info = sp.track(track_id)
print(f"✅ Connecté à Spotify !\nTitre : {track_info['name']}\nArtiste : {track_info['artists'][0]['name']}")
