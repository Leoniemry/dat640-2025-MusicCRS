import json
import os
import requests
from database import *

from collections import Counter


def get_artist_by_title(title: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT artist_name
        FROM Track
        WHERE LOWER(track_name) = LOWER(?)
    """, (title,))
    artists = [row[0] for row in cur.fetchall()]
    conn.close()

    if artists:
        artist_list = ", ".join(artists)
        return f"Here is a list of artists associated with '{title}': {artist_list}."
    else:
        return f"No artist found for '{title}'."

def get_album(artist: str, title: str):
    print(f"🔎 get_album() called with artist='{artist}' | title='{title}'")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT DISTINCT album_name
    FROM Track
    WHERE LOWER(track_name) LIKE LOWER(?) 
      AND LOWER(artist_name) LIKE LOWER(?)
    """, (f"%{title.strip()}%", f"%{artist.strip()}%"))

    rows = cur.fetchall()
    print(f"🧠 SQL returned {len(rows)} results: {rows[:3]}")

    conn.close()
    
    if rows:
        albums = [row[0] for row in rows]
        return f"'{title}' by {artist} appears in albums: {', '.join(albums[:5])}."
    else:
        return f"No album found for '{title}' by {artist}."


def get_track_popularity(artist: str, title: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(DISTINCT pt.pid)
        FROM PlaylistTrack pt
        JOIN Track t ON pt.track_uri = t.track_uri
        WHERE LOWER(t.track_name) = LOWER(?) AND LOWER(t.artist_name) = LOWER(?)
    """, (title, artist))
    result = cur.fetchone()
    conn.close()
    count = result[0] if result and result[0] else 0
    print(count)
    return f"The track '{title}' by {artist} appears in {count} playlists in the database."

def get_most_popular_song_by_artist(artist: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT artist_name
        FROM Track
        WHERE LOWER(artist_name) LIKE LOWER(?)
    """, (f"%{artist}%",))

    results = cur.fetchall()
    print("Matching artists:", results)

    if not results:
        conn.close()
        return f"No songs found for {artist}."
    chosen_artist = results[0][0]
    print("Using artist:", chosen_artist)

    cur.execute("""
        SELECT t.track_name, COUNT(pt.pid) AS playlist_count
        FROM Track t
        JOIN PlaylistTrack pt ON t.track_uri = pt.track_uri
        WHERE LOWER(t.artist_name) = LOWER(?)
        GROUP BY t.track_name
        ORDER BY playlist_count DESC
        LIMIT 1
    """, (chosen_artist.lower(),))

    result = cur.fetchone()
    conn.close()

    if result:
        track_name, count = result
        return f"The most popular song by {chosen_artist} is '{track_name}' ({count} playlists)."
    else:
        return f"No popular song found for {chosen_artist}."

def recommend_from_db(current_playlist_tracks):
    conn = get_connection()
    cur = conn.cursor()
    
    current_track_uris = [t.get("track_uri") or t.get("uri") for t in current_playlist_tracks]
    if not current_track_uris:
        conn.close()
        return []
    

    playlist_artists = {t.get("artist") for t in current_playlist_tracks if t.get("artist")}
    playlist_albums = {t.get("album_name") for t in current_playlist_tracks if t.get("album_name")}

    placeholders = ','.join(['?'] * len(current_track_uris))

    cur.execute(f"""
        SELECT pid, COUNT(*) as match_count
        FROM PlaylistTrack
        WHERE track_uri IN ({placeholders})
        GROUP BY pid
        ORDER BY match_count DESC
        LIMIT 50
    """, current_track_uris)
    related_playlists = cur.fetchall()
    if not related_playlists:
        conn.close()
        return []

    related_pids = [pid for pid, _ in related_playlists]

    placeholders_pids = ','.join(['?'] * len(related_pids))

    cur.execute(f"""
        SELECT pt.track_uri, tr.track_name, tr.artist_name, tr.album_name
        FROM PlaylistTrack pt
        JOIN Track tr ON pt.track_uri = tr.track_uri
        WHERE pt.pid IN ({placeholders_pids})
    """, related_pids)
    candidates = cur.fetchall() 

    freq_counter = {}
    for track_uri, track_name, artist_name, album_name in candidates:
        if track_uri not in current_track_uris: 
            key = (track_uri, track_name, artist_name, album_name)
            freq_counter[key] = freq_counter.get(key, 0) + 1

    sorted_candidates = sorted(freq_counter.items(), key=lambda x: x[1], reverse=True)

    recommendations = []
    for (track_uri, track_name, artist_name, album_name), freq in sorted_candidates:
        if album_name in playlist_albums:
            reason = "From the same album as one of your tracks"
        elif artist_name in playlist_artists:
            reason = "Same artist as one of your tracks"
        else:
            reason = f"Appears in {freq} playlists containing some of your songs"

        
        recommendations.append({
            "artist": artist_name,
            "title": track_name,
            "track_uri": track_uri,
            "reason": reason
        })
        if len(recommendations) >= 5:
            break

    conn.close()
    return recommendations
