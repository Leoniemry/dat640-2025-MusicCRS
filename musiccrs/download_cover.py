import os
import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials


CLIENT_ID = "6c5ce7f3ba45416ca6d5078ee52a6859"
CLIENT_SECRET = "4e3727af29a344cfb89732c9a1abfbdf"

def get_cover(track_uri):

    # ===Creating the outputfolder ===
    output_dir = "covers"
    os.makedirs(output_dir, exist_ok=True)

    # === Connect to spotify ===
    sp = Spotify(auth_manager=SpotifyClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    ))

    # ===Collecting the data of the song ===
    track = sp.track(track_uri)
    track_name = track["name"]
    artist_name = track["artists"][0]["name"]


    cover_url = track["album"]["images"][0]["url"]  
    print(f"Cover URL: {cover_url}")

    # === Downloading the cover ===
    image_data = requests.get(cover_url).content
    cover_filename = f"{artist_name} - {track_name}.jpg".replace("/", "-")
    cover_path = os.path.join(output_dir, cover_filename)

    with open(cover_path, "wb") as f:
        f.write(image_data)

    print(f"Cover téléchargée : {cover_path}")
    return cover_path
