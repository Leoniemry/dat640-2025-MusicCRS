import json
import os

database_path = "C:/Users/Basti/Desktop/Phelma/3A/Stavanger/DAT-640_Information_Retriaval_Text_Mining/Project/Git/dat640-2025-MusicCRS/musiccrs/data/spotify_million_playlist_dataset_challenge/challenge_set.json"

def load_database():
    with open(database_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tracks = []
    for playlist in data["playlists"]:
        for track in playlist["tracks"]:
            tracks.append({
                "artist": track["artist_name"],
                "title": track["track_name"],
                "uri": track["track_uri"]
            })
    return tracks
TRACKS = load_database()

def search_track(artist: str, title: str):
    artist, title = artist.lower(), title.lower()
    for t in TRACKS:
        if artist in t["artist"].lower() and title in t["title"].lower():
            return t
    return None