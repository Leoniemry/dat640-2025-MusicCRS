import os
import json
import sqlite3
from tqdm import tqdm


DATA_DIR = "musiccrs/data/mpd.v1/data"
DB_PATH = "musiccrs/data/music.db"


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()


cur.executescript("""
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
    album_name TEXT,
    artist_uri TEXT,
    artist_name TEXT,
    duration_ms INTEGER
);

CREATE TABLE IF NOT EXISTS Playlist (
    pid INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    collaborative BOOLEAN,
    modified_at INTEGER,
    num_tracks INTEGER,
    num_albums INTEGER,
    num_artists INTEGER,
    num_followers INTEGER,
    num_edits INTEGER,
    duration_ms INTEGER
);

CREATE TABLE IF NOT EXISTS PlaylistTrack (
    pid INTEGER,
    track_uri TEXT,
    pos INTEGER,
    PRIMARY KEY (pid, track_uri),
    FOREIGN KEY (pid) REFERENCES Playlist(pid),
    FOREIGN KEY (track_uri) REFERENCES Track(track_uri)
);
""")

conn.commit()


json_files = sorted(os.listdir(DATA_DIR))

for filename in tqdm(json_files, desc="Processing JSON slices"):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        slice_data = json.load(f)
        playlists = slice_data["playlists"]
        for playlist in playlists:
            # Playlist
            cur.execute("""
                INSERT OR IGNORE INTO Playlist(
                    pid, name, description, modified_at, num_artists, num_albums,
                    num_tracks, num_followers, num_edits, duration_ms, collaborative
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                playlist["pid"], playlist["name"], playlist.get("description"),
                playlist["modified_at"], playlist["num_artists"], playlist["num_albums"],
                playlist["num_tracks"], playlist["num_followers"], playlist["num_edits"],
                playlist["duration_ms"], playlist["collaborative"]
            ))

            for track in playlist["tracks"]:
                # Artist
                cur.execute("""
                    INSERT OR IGNORE INTO Artist(artist_uri, artist_name)
                    VALUES (?, ?)
                """, (track["artist_uri"], track["artist_name"]))

                # Album
                cur.execute("""
                    INSERT OR IGNORE INTO Album(album_uri, album_name, artist_uri)
                    VALUES (?, ?, ?)
                """, (track["album_uri"], track["album_name"], track["artist_uri"]))

                # Track
                cur.execute("""
                    INSERT OR IGNORE INTO Track(
                        track_uri, track_name, album_uri, album_name,
                        artist_uri, artist_name, duration_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    track["track_uri"], track["track_name"], track["album_uri"], track["album_name"],
                    track["artist_uri"], track["artist_name"], track["duration_ms"]
                ))

                # PlaylistTrack
                cur.execute("""
                    INSERT OR IGNORE INTO PlaylistTrack(pid, track_uri, pos)
                    VALUES (?, ?, ?)
                """, (playlist["pid"], track["track_uri"], track["pos"]))

    conn.commit()

conn.close()
print("Database created and populated successfully!")
