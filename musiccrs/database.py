import json
import os
import requests

database_path = "C:/Users/Basti/Desktop/Phelma/3A/Stavanger/DAT-640_Information_Retriaval_Text_Mining/Project/Git/dat640-2025-MusicCRS/musiccrs/data/spotify_million_playlist_dataset_challenge/challenge_set.json"

def load_database():
    # === Opening and loading the database === 
    with open(database_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tracks = []
    # === Extracting usefull data ===
    for playlist in data["playlists"]:
        for track in playlist["tracks"]:
            tracks.append({
                "artist": track["artist_name"],
                "title": track["track_name"],
                "uri": track["track_uri"],
                "album_name": track["album_name"]
            })
    return tracks

TRACKS = load_database()

def search_track(artist: str, title: str):
    artist, title = artist.lower(), title.lower()
    for t in TRACKS:
        if artist in t["artist"].lower() and title in t["title"].lower():
            return t
    return None

def search_track_title(title: str):
    result = []
    seen_artist = set()
    message =f"Several tracks found for'{title}';\n"
    for t in TRACKS:
        if title.lower() in t["title"].lower():
            artist_name = t['artist']
            if artist_name not in seen_artist:
                result.append(t)
                seen_artist.add(artist_name)    
    print(result)
    if result :   
        for i,r in enumerate(result,1):
            message +=f"{i}.{r['artist']} - {r['title']} ({r['album_name']})\n"
        message+="\n Please choose a number"
        
        return message, result
    return None