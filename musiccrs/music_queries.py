import json
import os
import requests
from database import *




def get_artist_by_title(title: str):
    title = title.lower()


def get_album_by_title(artist:str, title: str):
    result = search_track(artist,title)
    albums = set(result.get("album_name") for t in result)
    return f"'{title}' appears in albums: {', '.join(list(albums)[:5])}."

def get_track_popularity(title: str):
    ...

def get_most_popular_song_by_artist(artist: str):
    ...