import json
import os
import requests
from collections import Counter
import sqlite3
import pandas as pd

DB_PATH = "musiccrs/data/music.db"
database_small_path ="C:/Users/Basti/Desktop/Phelma/3A/Stavanger/DAT-640_Information_Retriaval_Text_Mining/Project/Git/dat640-2025-MusicCRS/musiccrs/data/spotify_million_playlist_dataset_challenge/challenge_set.json"
database_path = "C:/Users/Basti/Desktop/Phelma/3A/Stavaop/Phelma/3A/Stavanger/DAT-640_Information_Retriaval_Text_Mining/Project/Git/dat640-2025-MusicCRS2/musiccrs/data/spotify_million_playlist_dataset_challenge/cnger/DAT-640_Information_Retriaval_Text_Mining/Project/Git/dat640-2025-MusicCRS/musiccrs/data/mpd.v1/data"
merged_path = os.path.join(database_path, "all_tracks.json")

DB_PATH = "musiccrs/data/music.db"  # adapte selon ton chemin

# === Connexion ===
conn = sqlite3.connect(DB_PATH)

# === Voir les tables disponibles ===
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
print("📂 Tables disponibles :")
print(tables)

# === Charger les 1000 premières lignes ===
df = pd.read_sql_query("SELECT * FROM Track LIMIT 1000;", conn)

# === Afficher sans coupure ===
pd.set_option("display.max_rows", None)      # affiche toutes les lignes
pd.set_option("display.max_columns", None)   # affiche toutes les colonnes
pd.set_option("display.width", 0)            # permet d'afficher toute la largeur
pd.set_option("display.max_colwidth", None)  # pas de troncature des textes longs

print("\n🎵 === 1000 premières lignes de la table Track ===")
print(df)

# === Si tu veux voir juste les 3 colonnes importantes ===
print("\n🎶 === artist_name, track_name, album_name ===")
df_small = pd.read_sql_query(
    "SELECT artist_name, track_name, album_name FROM Track LIMIT 1000;",
    conn
)
print(df_small)

# === Fermeture ===
conn.close()


def get_connection():
    return sqlite3.connect(DB_PATH)


def load_database():
    if os.path.exists(merged_path):
        with open(merged_path, "r", encoding="utf-8") as f:
            tracks = json.load(f)
        print(f"✅ Database merged charged : ({len(tracks)} tracks).")
        return tracks

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
                            "album_name": track.get("album_name", ""),
                            "duration":track.get("duration_ms","") 
                        })
            except Exception as e:
                print(f"Error {filename}: {e}")
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(tracks, f, indent=2, ensure_ascii=False)
    
    print(f"Merged file saved  : ({len(tracks)} morceaux).")
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
                "album_name": track["album_name"],
                 "duration":track.get("duration_ms","") 
                   })
    return tracks

TRACKS = load_small_database()

def search_track(artist: str, title: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT artist_name, track_name, track_uri, album_name, duration_ms
        FROM Track
        WHERE LOWER(artist_name) LIKE ? AND LOWER(track_name) LIKE ?
        LIMIT 1
    """, (f"%{artist.lower()}%", f"%{title.lower()}%"))
    result = cur.fetchone()
    conn.close()

    if result:
        artist, t, uri, album, duration = result
        return {
            "artist": artist,
            "title": t,
            "uri": uri,
            "album_name": album,
            "duration": duration
        }
    else:
        return None


def popularity():
    artist_counts = Counter(t["artist"] for t in TRACKS)
    return artist_counts



def search_track_title(title: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT artist_name, track_name, track_uri, album_name, duration_ms FROM Track WHERE LOWER(track_name) = ?", (title.lower(),))
    result = cur.fetchall()
    conn.close()

    if not result:
        return None, None

    message = f"Several tracks found for '{title}':\n"
    unique_result = []
    seen_artists = set()
    for row in result:
        artist, t, uri, album, duration = row
        if artist not in seen_artists:
            unique_result.append({"artist": artist, "title": t, "uri": uri, "album_name": album, "duration": duration})
            seen_artists.add(artist)
            message += f"{len(unique_result)}. {artist} - {t} ({album})\n"
            if len(unique_result) >= 5:
                break
    return message, unique_result