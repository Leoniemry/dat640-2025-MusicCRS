import sqlite3

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
    duration_ms INTEGER,
    FOREIGN KEY (album_uri) REFERENCES Album(album_uri)
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
    PRIMARY KEY (pid, pos),
    FOREIGN KEY (pid) REFERENCES Playlist(pid),
    FOREIGN KEY (track_uri) REFERENCES Track(track_uri)
);
""")

conn.commit()
conn.close()
print("✅ Base de données créée : music.db")
