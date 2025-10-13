import os
import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials


CLIENT_ID = "b408182a8de64714ad698d1841704963"
CLIENT_SECRET = "82d8b8299a374b7686b613c3db446819"

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
    preview_url = track["preview_url"]


    cover_url = track["album"]["images"][0]["url"]  
    print(f"Cover URL: {cover_url}")

    # === Downloading the cover ===
    image_data = requests.get(cover_url).content
    cover_filename = f"{artist_name} - {track_name}.jpg".replace("/", "-")
    cover_path = os.path.join(output_dir, cover_filename)

    with open(cover_path, "wb") as f:
        f.write(image_data)

    print(f"Cover téléchargée : {cover_path}")
    return cover_url,preview_url
