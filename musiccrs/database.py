import json
import os
import requests
from collections import Counter

database_small_path ="C:/Users/Basti/Desktop/Phelma/3A/Stavanger/DAT-640_Information_Retriaval_Text_Mining/Project/Git/dat640-2025-MusicCRS/musiccrs/data/spotify_million_playlist_dataset_challenge/challenge_set.json"
database_path = "C:/Users/Basti/Desktop/Phelma/3A/Stavaop/Phelma/3A/Stavanger/DAT-640_Information_Retriaval_Text_Mining/Project/Git/dat640-2025-MusicCRS/musiccrs/data/spotify_million_playlist_dataset_challenge/cnger/DAT-640_Information_Retriaval_Text_Mining/Project/Git/dat640-2025-MusicCRS/musiccrs/data/mpd.v1/data"
merged_path = os.path.join(database_path, "all_tracks.json")

def load_database():
    """Charge tous les fichiers JSON du dossier et crée un all_tracks.json fusionné"""
    # Si le fichier fusionné existe déjà → le charger directement
    if os.path.exists(merged_path):
        with open(merged_path, "r", encoding="utf-8") as f:
            tracks = json.load(f)
        print(f"✅ Base fusionnée chargée ({len(tracks)} morceaux).")
        return tracks

    # Sinon, parcourir tous les fichiers JSON et fusionner
    tracks = []
    for filename in os.listdir(database_path):
        if filename.endswith(".json") and filename != "all_tracks.json":
            filepath = os.path.join(database_path, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for playlist in data.get("playlists", []):
                    for track in playlist.get("tracks", []):
                        tracks.append({
                            "artist": track.get("artist_name", ""),
                            "title": track.get("track_name", ""),
                            "uri": track.get("track_uri", ""),
                            "album_name": track.get("album_name", "")
                        })
            except Exception as e:
                print(f"⚠️ Erreur chargement {filename}: {e}")
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(tracks, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Fichier fusionné sauvegardé ({len(tracks)} morceaux).")
    return tracks


def load_small_database():
     # === Opening and loading the database === 
    with open(database_small_path, "r", encoding="utf-8") as f:
         data = json.load(f) 
    tracks = [] 
    # === Extracting usefull data === 
    for playlist in data["playlists"]: 
        for track in playlist["tracks"]: 
            tracks.append({ 
                "artist": track["artist_name"],
                "title": track["track_name"], 
                "uri": track["track_uri"],
                "album_name": track["album_name"] })
    return tracks

TRACKS = load_small_database()

def search_track(artist: str, title: str):
    artist, title = artist.lower(), title.lower()
    for t in TRACKS:
        if artist in t["artist"].lower() and title in t["title"].lower():
            return t
    return None


def popularity():
    artist_counts = Counter(t["artist"] for t in TRACKS)
    return artist_counts



def search_track_title(title: str):
    message =f"Several tracks found for'{title}';\n"
    artist_counts = popularity()
    result = [t for t in TRACKS if title.lower() in t["title"].lower()]
    result_sorted = sorted(result,key=lambda x: (-artist_counts[x['artist']], x['artist'].lower()))
    if not result : 
        return None, None
    unique_result=[] 
    unique_result_name = []
    seen_artist = set()
    for r in result_sorted:
        artist_name  = r["artist"]
        if artist_name not in seen_artist:
            unique_result_name.append(artist_name)
            unique_result.append(r)
            seen_artist.add(artist_name)

    for i, r in enumerate(unique_result, 1):
        if i > 5 :
            break
        message += f"{i}. {r['artist']} - {r['title']} ({r.get('album_name', 'Unknown album')})\n"
    message += "\nPlease choose a number."
    return message, unique_result 
   