import os
import json
import sqlite3

DATA_DIR = "musiccrs/data/mpd.v1/data"
DB_PATH = "musiccrs/data/music.db"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()


cur.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Artist (
    artist_uri TEXT PRIMARY KEY,
    artist_name TEXT
);

CREATE TABLE IF NOT EXISTS Album (
    album_uri TEXT PRIMARY KEY,
    album_name TEXT,
    artist_uri TEXT,
    FOREIGN KEY (artist_uri) REFERENCES Artist(artist_uri)
);

CREATE TABLE IF NOT EXISTS Track (
    track_uri TEXT PRIMARY KEY,
    track_name TEXT,
    album_uri TEXT,
    artist_uri TEXT,
    duration_ms INTEGER,
    FOREIGN KEY (album_uri) REFERENCES Album(album_uri),
    FOREIGN KEY (artist_uri) REFERENCES Artist(artist_uri)
);

CREATE TABLE IF NOT EXISTS Playlist (
    pid INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    modified_at INTEGER,
    num_artists INTEGER,
    num_albums INTEGER,
    num_tracks INTEGER,
    num_followers INTEGER,
    num_edits INTEGER,
    duration_ms INTEGER,
    collaborative BOOLEAN
);

CREATE TABLE IF NOT EXISTS PlaylistTrack (
    pid INTEGER,
    track_uri TEXT,
    pos INTEGER,
    PRIMARY KEY(pid, track_uri),
    FOREIGN KEY(pid) REFERENCES Playlist(pid),
    FOREIGN KEY(track_uri) REFERENCES Track(track_uri)
);
""")
conn.commit()

# Nombre de ficheir à traiter
MAX_SLICES = 100

json_files = sorted(os.listdir(DATA_DIR))[:MAX_SLICES]

for filename in json_files:
    filepath = os.path.join(DATA_DIR, filename)
    print(f"Processing {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        slice_data = json.load(f)
        playlists = slice_data.get("playlists", [])
        for playlist in playlists:
            
            cur.execute("""
                INSERT OR IGNORE INTO Playlist(pid, name, description, modified_at, num_artists, num_albums, num_tracks, num_followers, num_edits, duration_ms, collaborative)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                playlist.get("pid"),
                playlist.get("name"),
                playlist.get("description"),
                playlist.get("modified_at"),
                playlist.get("num_artists"),
                playlist.get("num_albums"),
                playlist.get("num_tracks"),
                playlist.get("num_followers"),
                playlist.get("num_edits"),
                playlist.get("duration_ms"),
                1 if str(playlist.get("collaborative")).lower() in ("true","1") else 0
            ))

            for track in playlist.get("tracks", []):
                
                artist_uri = track.get("artist_uri")
                artist_name = track.get("artist_name")
                album_uri = track.get("album_uri")
                album_name = track.get("album_name")
                track_uri = track.get("track_uri")
                track_name = track.get("track_name")
                duration_ms = track.get("duration_ms")

                if artist_uri and artist_name:
                    cur.execute("""
                        INSERT OR IGNORE INTO Artist(artist_uri, artist_name) VALUES (?, ?)
                    """, (artist_uri, artist_name))

                if album_uri and album_name:
                    
                    cur.execute("""
                        INSERT OR IGNORE INTO Album(album_uri, album_name, artist_uri) VALUES (?, ?, ?)
                    """, (album_uri, album_name, artist_uri))


                if track_uri and track_name:
                    cur.execute("""
                        INSERT OR IGNORE INTO Track(track_uri, track_name, album_uri, artist_uri, duration_ms)
                        VALUES (?, ?, ?, ?, ?)
                    """, (track_uri, track_name, album_uri, artist_uri, duration_ms))


                if playlist.get("pid") is not None and track_uri:
                    cur.execute("""
                        INSERT OR IGNORE INTO PlaylistTrack(pid, track_uri, pos) VALUES (?, ?, ?)
                    """, (playlist.get("pid"), track_uri, track.get("pos")))

    conn.commit()

conn.close()
print(f"Database populated with first {len(json_files)} slice files!")
