"""MusicCRS conversational agent."""

import ollama
from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.intent import Intent
from dialoguekit.core.slot_value_annotation import SlotValueAnnotation
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.agent import Agent
from dialoguekit.participant.participant import DialogueParticipant
from dialoguekit.platforms import FlaskSocketPlatform
from database import *
from download_cover import get_cover
from music_queries import *
import spotipy
from spotipy.oauth2 import SpotifyOAuth
# from play_spotify import*


OLLAMA_HOST = "https://ollama.ux.uis.no"
OLLAMA_MODEL = "llama3.3:70b"
OLLAMA_API_KEY = "SET YOUR API KEY HERE"

_INTENT_OPTIONS = Intent("OPTIONS")


class MusicCRS(Agent):
    def __init__(self, use_llm: bool = True):
        """Initialize MusicCRS agent."""
        super().__init__(id="MusicCRS")

        if use_llm:
            self._llm = ollama.Client(
                host=OLLAMA_HOST,
                headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
            )
        else:
            self._llm = None

        self._playlists = {"default":{"tracks" : [],"cover" : None}}  # Stores the current playlist
        self._current_playlist = "default"
        self._pending_recommendations = None

    def welcome(self) -> None:
        """Sends the agent's welcome message."""
        utterance = AnnotatedUtterance(
            "Hello, I'm MusicCRS. What are you in the mood for?",
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def goodbye(self) -> None:
        """Quits the conversation."""
        utterance = AnnotatedUtterance(
            "It was nice talking to you. Bye",
            dialogue_acts=[DialogueAct(intent=self.stop_intent)],
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def receive_utterance(self, utterance: Utterance) -> None:
        """Gets called each time there is a new user utterance.

        For now the agent only understands specific command.

        Args:
            utterance: User utterance.
        """
        response = ""
        dialogue_acts = []
        if utterance.text.startswith("/info"):
            response = self._list_info().replace("\t", "&emsp;").replace("\n", "<br>")

        elif utterance.text.startswith("/play"):
            track = utterance.text[6:].strip()  
            response = self._preview(track).replace("\n", "<br>")

        elif utterance.text.startswith("/add_title"):
            track = utterance.text[10:].strip()  
            response = self._select_track(track).replace("\n", "<br>")

        elif hasattr(self, "_pending_selection") and self._pending_selection:
            user_input = utterance.text.strip().lower()
            if user_input == "quit":
                response = "Selection cancelled."
                self._pending_selection = None
            else:
                try:
                    number = int(user_input)
                except ValueError:
                    response = "Please enter a valid number or type 'quit' to cancel."
                else:
                    result = self._pending_selection
                    response = self._add_track_title(title="", number=number, result=result).replace("\n", "<br>")
                    self._pending_selection = None
        elif utterance.text.startswith("/add"):
            track = utterance.text[5:].strip()  
            response = self._add_track(track).replace("\n", "<br>")
        elif utterance.text.startswith("/remove"):
            track = utterance.text[8:].strip().replace("\n", "<br>")
            response = self._remove_track(track)
        elif utterance.text == "/view":
            response = self._view_playlist().replace("\n", "<br>")
        elif utterance.text == "/clear":
            response = self._clear_playlist().replace("\n", "<br>")
        elif utterance.text.startswith("/switch"):
            playlist_name = utterance.text[8:].strip().replace("\n", "<br>")
            response = self._switch_playlist(playlist_name)
        elif utterance.text.startswith("/create"):
            playlist_name = utterance.text[7    :].strip()
            response = self._create_playlist(playlist_name).replace("\n", "<br>")

        elif utterance.text.startswith("/ask_track"):
            question = utterance.text[len("/ask_track"):].strip().lower()

            if "artist of" in question:
                title = question.split("artist of")[-1].strip()
                print(title)
                response = self._get_artist_by_title(title).replace("\n", "<br>")
                

            elif "album" in question:
                query = utterance.text[len("/ask_track"):].strip()

                for keyword in ["In which album appears", "contains", "please", "user", "thanks"]:
                    query = query.replace(keyword, "").strip()

                parts = query.split()
                if len(parts) >= 2:
                    artist, title = [s.strip() for s in query.split(":", 1)]
                    print("Artist:", artist)
                    print("Title:", title)
                    response = get_album(artist, title).replace("\n", "<br>")
                else:
                    response = "Please specify both artist and title."





            elif "popular song by" in question:
                artist = question.split("popular song by")[-1].strip()
                response = self._get_most_popular_song_by_artist(artist).replace("\n", "<br>")

            elif "how many playlists" in question or "appear" in question:

                query = question
                query = query.replace("how many playlists", "").replace("appears", "").replace("appear","").replace("how many playlist", "").strip()
               
                if ":" in query:
                    artist, title = [s.strip() for s in query.split(":", 1)]
                    print(artist)
                    print(title)
                    response = self._get_track_popularity(artist, title).replace("\n", "<br>")
                else:
                    response = "Please specify both artist and title using 'Artist:Title'."
                    
        elif utterance.text.startswith("/stat"):
            prompt =utterance.text[6:]
            response = self._playlist_summary()
        elif utterance.text.startswith("/ask_llm "):
            prompt = utterance.text[9:]
            response = self._ask_llm(prompt)
        elif utterance.text.startswith("/options"):
            options = [
                "Play some jazz music",
                "Recommend me some pop songs",
                "Create a workout playlist",
            ]
            response = self._options(options)
            dialogue_acts = [
                DialogueAct(
                    intent=_INTENT_OPTIONS,
                    annotations=[
                        SlotValueAnnotation("option", option) for option in options
                    ],
                )
            ]
        elif utterance.text.startswith("/recommend"):
            response = self._recommend_songs().replace("\n", "<br>")

        elif hasattr(self, "_pending_recommendations") and self._pending_recommendations:
            user_input = utterance.text.strip().lower()

            if user_input == "quit":
                response = "Selection cancelled."
                self._pending_recommendations = None
            else:
                try:
                    # Sélection par espaces
                    indices = [int(x)-1 for x in user_input.split()]
                except ValueError:
                    response = "Invalid input. Enter numbers separated by spaces or type 'quit' to cancel."
                else:
                    added_tracks = []
                    invalid_indices = False
                    for idx in indices:
                        if 0 <= idx < len(self._pending_recommendations):
                            track = self._pending_recommendations[idx]
                            self._playlists[self._current_playlist]["tracks"].append(track)
                            added_tracks.append(f"{track['artist']} – {track['title']}")
                        else:
                            invalid_indices = True

                    if invalid_indices:
                        response = "One or more numbers are out of range. Selection cancelled."
                    elif added_tracks:
                        self._emit_playlist_update()
                        response = "Added:\n" + "\n".join(added_tracks)
                    else:
                        response = "No valid selections made."
                    response = response.replace("\n", "<br>")
                    self._pending_recommendations = None

        elif utterance.text.startswith("/auto_playlist"):
            description = utterance.text[len("/auto_playlist"):].strip()
            response = self._create_auto_playlist(description).replace("\n", "<br>")





        elif utterance.text == "/quit":
            self.goodbye()
            return
        else:
            response = "I'm sorry, I don't understand that command."
        self._dialogue_connector.register_agent_utterance(
            AnnotatedUtterance(
                response,
                participant=DialogueParticipant.AGENT,
                dialogue_acts=dialogue_acts,
            )
        )

    # --- Response handlers ---

    def _info(self) -> str:
        """Gives information about the agent."""
        return "I am MusicCRS, a conversational recommender system for music."

    def _ask_llm(self, prompt: str) -> str:
        """Calls a large language model (LLM) with the given prompt.

        Args:
            prompt: Prompt to send to the LLM.

        Returns:
            Response from the LLM.
        """
        if not self._llm:
            return "The agent is not configured to use an LLM"

        llm_response = self._llm.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "stream": False,
                "temperature": 0.7,  # optional: controls randomness
                "max_tokens": 100,  # optional: limits the length of the response
            },
        )

        return f"LLM response: {llm_response['response']}"

    def _options(self, options: list[str]) -> str:
        """Presents options to the user."""
        return (
            "Here are some options:\n<ol>\n"
            + "\n".join([f"<li>{option}</li>" for option in options])
            + "</ol>\n"
        )
    

    def _add_track_title(self,title : str, number : str,result :list):
        if not result or number < 1 or number > len(result):
            return "Invalid selection."

        playlist_data = self._playlists[self._current_playlist]
        playlist = playlist_data["tracks"]
        selected_track = result[number-1]
        a_norm = selected_track['artist'].lower()
        t_norm = selected_track['title'].lower()

        for item in playlist:
            if isinstance(item, dict):
                if a_norm == item.get('artist', '').lower() and t_norm == item.get('title', '').lower():
                    return f"'{selected_track['artist']} – {selected_track['title']}' is already in playlist '{self._current_playlist}'."
        playlist.append(selected_track)
       
        if not playlist_data["cover"]:
            cover_url,_ = get_cover(selected_track["uri"])
            if cover_url:
                playlist_data["cover"] = cover_url
        self._emit_playlist_update()
        return f"Added '{selected_track['artist']} – {selected_track['title']}' to playlist '{self._current_playlist}'."


    def _select_track(self,track: str):
        title =  track.strip()
        message, result = search_track_title(title)
        if not result :
            return f"Not found in database"
        self._pending_selection = result  
        message += "\nPlease choose a number."
        return f"{message}\n"

    def _add_track(self, track: str) -> str:
        if ":" not in track :
            return f'Wrong format if you want to use only title use /add_title'

        else :
            artist, title = [s.strip() for s in track.split(":", 1)]
            print("Artist:",artist)
            print("Title : ",title)
            result = search_track(artist, title)    
            if not result:
                return f"'{artist}: {title}'not found in database."
            playlist_data = self._playlists[self._current_playlist]
            playlist = playlist_data["tracks"]

            a_norm = result.get("artist", artist).lower()
            t_norm = result.get("title", title).lower()

            for item in playlist:
                if isinstance(item, dict):
                    if a_norm == item.get("artist", "").lower() and t_norm == item.get("title", "").lower():
                        return f"'{result.get('artist')} – {result.get('title')}'is already in playlist'{self._current_playlist}'." 
            playlist.append(result)

        if not playlist_data["cover"]:
            cover_url,_ = get_cover(result["uri"])
            if cover_url:
                playlist_data["cover"] = cover_url
        self._emit_playlist_update()
        return f"Added '{result.get('artist', artist)} – {result.get('title', title)}' to playlist '{self._current_playlist}'."
        
    def _remove_track(self, track: str) -> str:
        if ":" not in track:
            return "Invalid syntax, please use Artist:Song."

        artist, title = [s.strip().lower() for s in track.split(":", 1)]
        playlist_data = self._playlists[self._current_playlist]
        playlist_tracks = playlist_data["tracks"]

        for item in playlist_tracks[:]: 
            if isinstance(item, dict):
                if artist in item.get("artist", "").lower() and title in item.get("title", "").lower():
                    playlist_tracks.remove(item)
                    if not playlist_data["tracks"]:
                        playlist_data["cover"] = None
                    self._emit_playlist_update()
                    return f"Deleted '{item.get('artist')} – {item.get('title')}' from playlist '{self._current_playlist}'."
            else:
                s = item.lower()
                if artist in s and title in s:
                    playlist_tracks.remove(item)
                    if not playlist_data["tracks"]:
                        playlist_data["cover"] = None
                    self._emit_playlist_update()
                    return f"Deleted '{item}' from playlist '{self._current_playlist}'."

        return f"Song '{track}' not found in playlist '{self._current_playlist}'."

    def _view_playlist(self) -> str:
        playlist_data = self._playlists[self._current_playlist]
        playlist = playlist_data["tracks"]
        if not playlist:
            return f"Playlist '{self._current_playlist}' is empty."

        message = f" Playlist '{self._current_playlist}':\n"
        for i, item in enumerate(playlist, 1):
            if isinstance(item, dict):
                message += f"{i}. {item.get('artist')} – {item.get('title')}\n"
            else:
                message += f"{i}. {item}\n"

        print(playlist_data)
        return message.strip()

    def _clear_playlist(self) -> str:
        playlist_data = self._playlists[self._current_playlist]
        playlist_data["tracks"].clear()
        playlist_data["cover"] = None 
        self._emit_playlist_update()
        return f"Playlist '{self._current_playlist}'now empty."

    def _switch_playlist(self, name: str) -> str:
        if name in self._playlists:
            self._current_playlist = name
            self._emit_playlist_update()
            return f"Switched to playlist '{name}'."
        return f"Playlist '{name}' does not exist."

    def _create_playlist(self, name: str) -> str:
        if name in self._playlists:
            return f"Playlist '{name}' already exists."
        self._playlists[name] = {"tracks":[],"cover":None}
        self._current_playlist = name
        self._emit_playlist_update()
        return f"Created and switched to new playlist '{name}'."
    
    def _get_album(self,artist : str,title : str) -> str:
        print(artist,title)
        return get_album(artist,title)

    def _get_artist_by_title(self, title: str):
        return get_artist_by_title(title)

    def _get_track_popularity(self, artist:str, title: str):
        return get_track_popularity(artist,title)

    def _get_most_popular_song_by_artist(self, artist: str):
        return get_most_popular_song_by_artist(artist)

    def _list_info(self):
        message ="Here is a list of options you can use with the ChatBot: \n " \
        "Here you will see the description of the command----> Here you will the command itself '/command'\n" \
        "You can create multiple playlists and name it ----> /create 'Name'\n" \
        "You can switch to another playlist ----> /switch 'Name'\n" \
        "You can add a song with the artist and the title ----> /add 'Artist':'Title'\n" \
        "You can add a song with title only and select the artist that you want ----> /add_title 'Title'\n" \
        "You can remove a song from your playlist ----> /remove 'Artist':'Title'\n" \
        "You can view your playlist ----> /view \n" \
        "You can ask questions about tracks here is a list of the questions :\n" \
        "   \t\t----->/ask_track What is the most popular song of 'Artist'\n" \
        "   \t\t----->/ask_track In which album contains 'Artist':'Title'\n" \
        "   \t\t----->/ask_track In how many playlists appears 'Artist':'Title'\n" \
        "   \t\t----->/ask_track Who is the artist of 'Title\n" \
        "You can get song recommendations based on your current playlist ----> /recommend"
        return message




    def _playlist_summary(self):
        playlist_data = self._playlists[self._current_playlist]
        tracks = playlist_data["tracks"]

    
        if not tracks:
            return "The playlist is empty."

        total_duration_ms = 0
        artist_counts = {}
        album_counts = {}

        for track in tracks:
           
            total_duration_ms += track.get("duration", 0)

           
            artist = track.get("artist", "Unknown")
            artist_counts[artist] = artist_counts.get(artist, 0) + 1

            album = track.get("album_name", "Unknown album")
            album_counts[album] = album_counts.get(album, 0) + 1

        
        total_duration_min = total_duration_ms / 60000
        most_common_artist = max(artist_counts, key=artist_counts.get)
        most_common_album = max(album_counts, key=album_counts.get)
        unique_artists = len(artist_counts)
   
        message = (
            f"<b> Playlist Summary</b><br>"
            f"Total tracks: {len(tracks)}<br>"
            f"Total duration: {total_duration_min:.1f} minutes<br>"
            f"Most frequent artist: {most_common_artist} ({artist_counts[most_common_artist]} songs)<br>"
            f"Most frequent album: {most_common_album} ({album_counts[most_common_album]} songs)<br>"
            f"Number of unique artists: {unique_artists}<br>"
        )
        return message

    def _preview(self, track: str):    
        artist, title = [s.strip() for s in track.split(":", 1)]
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id="b408182a8de64714ad698d1841704963",
            client_secret="82d8b8299a374b7686b613c3db446819",
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="user-read-playback-state,user-modify-playback-state,streaming"
        ))

        query = f"{artist} {title}"
        results = sp.search(q=query, type="track", limit=1)

        if not results["tracks"]["items"]:
            return f"Aucun morceau trouvé pour {artist} - {title}"

        track = results["tracks"]["items"][0]
        track_name = track["name"]
        artist_name = track["artists"][0]["name"]
        preview_url = track.get("preview_url")
        spotify_url = track["external_urls"]["spotify"]
        print(results)
        if not preview_url:
            return f"""
            No preview avaible for {artist_name} - {track_name}.<br>
            🔗 <a href="{spotify_url}" target="_blank">Listen on spotify</a>
            """

        html_preview = f"""
        🎵 {artist_name} - {track_name}<br>
        <audio controls>
            <source src="{preview_url}" type="audio/mpeg">
            Votre navigateur ne supporte pas la lecture audio.
        </audio><br>
        🔗 <a href="{spotify_url}" target="_blank">Listen on spotify</a>
        """
        return html_preview

    def _emit_playlist_update(self):
        playlist_data = self._playlists[self._current_playlist]
        # On envoie un message spécial que le frontend peut reconnaître
        self._dialogue_connector.register_agent_utterance(
            AnnotatedUtterance(
                f"PLAYLIST_UPDATE::{self._current_playlist}::{json.dumps(playlist_data)}",
                participant=DialogueParticipant.AGENT
            )
        )

    def _recommend_songs(self):
        current_playlist = self._playlists[self._current_playlist]["tracks"]
        if not current_playlist:
            return "Your playlist is empty. Please add a few song first."
        recommendations = recommend_from_db(current_playlist)
        self._pending_recommendations = recommendations

        response = "<b>Recommended songs:</b><br>"
        for i, r in enumerate(recommendations, 1):
            response += f"<b>{i}. {r['artist']} - {r['title']}</b> ({r['reason']})<br>"
        response += "<br>Please select the songs to add by typing their numbers separated by spaces, or type 'quit' to cancel."
        return response


    def _create_auto_playlist(self, description: str):
        """Crée une nouvelle playlist automatiquement selon une description."""
        if not description:
            return "Please provide a description (e.g., /auto_playlist sad love songs)."

        
        playlist_name = description.replace(" ", "_").lower()

        if playlist_name in self._playlists:
            return f"A playlist '{playlist_name}' already exists."

        
        self._playlists[playlist_name] = {"tracks": [], "cover": None}
        self._current_playlist = playlist_name

        
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id="b408182a8de64714ad698d1841704963",
            client_secret="82d8b8299a374b7686b613c3db446819",
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="user-read-playback-state,user-modify-playback-state,streaming"
        ))


        
        results = sp.search(q=description, type="track", limit=10)
        items = results.get("tracks", {}).get("items", [])

        if not items:
            return f"No tracks found for '{description}'."

        added_tracks = []
        for track in items:
            info = {
                "artist": track["artists"][0]["name"],
                "title": track["name"],
                "album_name": track["album"]["name"],
                "uri": track["uri"],
                "duration": track["duration_ms"],
            }
     
            self._playlists[playlist_name]["tracks"].append(info)
            added_tracks.append(f"{info['artist']} – {info['title']}")


        cover_url = items[0]["album"]["images"][0]["url"] if items[0]["album"]["images"] else None
        if cover_url:
            self._playlists[playlist_name]["cover"] = cover_url

        self._emit_playlist_update()

        return f"🎶 Created playlist '<b>{playlist_name}</b>' based on '{description}' with {len(added_tracks)} songs:<br>" + "<br>".join(added_tracks)







if __name__ == "__main__":
    platform = FlaskSocketPlatform(MusicCRS)
    platform.start()
    platform.start()
