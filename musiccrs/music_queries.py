import json
import os
import requests
from database import *




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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT DISTINCT album_name
    FROM Track
    WHERE LOWER(track_name) LIKE LOWER(?) AND LOWER(artist_name) LIKE LOWER(?)
    """, (title, artist))

    albums = [row[0] for row in cur.fetchall()]
    conn.close()

    if albums:
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