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
            response = self._info()




        elif utterance.text.startswith("/add_title"):
            track = utterance.text[10:].strip()  
            response = self._select_track(track)
        elif hasattr(self, "_pending_selection") and self._pending_selection:
            try:
                number = int(utterance.text.strip())
            except ValueError:
                response = "Please enter a valid number."
            else:
                result = self._pending_selection
                response = self._add_track_title(title="", number=number, result=result)
                self._pending_selection = None  
        elif utterance.text.startswith("/add"):
            track = utterance.text[5:].strip()  
            response = self._add_track(track)
        elif utterance.text.startswith("/remove"):
            track = utterance.text[8:].strip()
            response = self._remove_track(track)
        elif utterance.text == "/view":
            response = self._view_playlist()
        elif utterance.text == "/clear":
            response = self._clear_playlist()
        elif utterance.text.startswith("/switch"):
            playlist_name = utterance.text[8:].strip()
            response = self._switch_playlist(playlist_name)
        elif utterance.text.startswith("/create"):
            playlist_name = utterance.text[7    :].strip()
            response = self._create_playlist(playlist_name)



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
            cover_url = get_cover(selected_track["uri"])
            if cover_url:
                playlist_data["cover"] = cover_url
        return f"Added '{selected_track['artist']} – {selected_track['title']}' to playlist '{self._current_playlist}'."


    def _select_track(self,track: str):
        title =  track.strip()
        message, result = search_track_title(title)
        self._pending_selection = result  
        return f"{message}\n Please select a number:"

    def _add_track(self, track: str) -> str:
        if ":" not in track :
            return f'Wrong format if you want to use only title use /addt'

        else :
            artist, title = [s.strip() for s in track.split(":", 1)]
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
            cover_url = get_cover(result["uri"])
            if cover_url:
                playlist_data["cover"] = cover_url
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
                    return f"Deleted '{item.get('artist')} – {item.get('title')}' from playlist '{self._current_playlist}'."
            else:
                s = item.lower()
                if artist in s and title in s:
                    playlist_tracks.remove(item)
                    return f"Deleted '{item}' from playlist '{self._current_playlist}'."

        return f"Song '{track}' not found in playlist '{self._current_playlist}'."

    def _view_playlist(self) -> str:
        playlist_data = self._playlists[self._current_playlist]
        playlist = playlist_data["tracks"]
        if not playlist:
            return f"🎧 Playlist '{self._current_playlist}' est vide."

        message = f"🎶 Playlist '{self._current_playlist}':\n"
        for i, item in enumerate(playlist, 1):
            if isinstance(item, dict):
                message += f"{i}. {item.get('artist')} – {item.get('title')}\n"
            else:
                message += f"{i}. {item}\n"

        if playlist_data["cover"]:
            message += f"\n🖼️ Cover: {playlist_data['cover']}"
        return message.strip()

    def _clear_playlist(self) -> str:
        playlist_data = self._playlists[self._current_playlist]
        playlist_data["tracks"].clear()
        playlist_data["cover"] = None 
        return f"Playlist '{self._current_playlist}'now empty."

    def _switch_playlist(self, name: str) -> str:
        if name in self._playlists:
            self._current_playlist = name
            return f"Switched to playlist '{name}'."
        return f"Playlist '{name}' does not exist."

    def _create_playlist(self, name: str) -> str:
        if name in self._playlists:
            return f"Playlist '{name}' already exists."
        self._playlists[name] = {"tracks":[],"cover":None}
        self._current_playlist = name
        return f"Created and switched to new playlist '{name}'."





if __name__ == "__main__":
    platform = FlaskSocketPlatform(MusicCRS)
    platform.start()
    platform.start()
