import "./PlaylistPanel.css"

import React, { useState } from "react";

import {
  MDBCard,
  MDBCardHeader,
  MDBCardBody,
  MDBIcon,
  MDBCardFooter,
} from "mdb-react-ui-kit";
import { on } from "events";

type Track = {
  artist: string;
  title: string;
};

type PlaylistData = {
  name: string;
  tracks: Track[];
};

interface PlaylistPanelProps {
  playlist: PlaylistData;
  onAddSong: (songText: string) => void;
  onRemoveSong: (songText: string) => void;
}

export default function PlaylistPanel({ playlist, onAddSong, onRemoveSong }: PlaylistPanelProps) {
  const [songInput, setSongInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!songInput.trim()) return;
    onAddSong(songInput.trim());
    setSongInput("");
  };

  const handleRemoveTrack = (index: number) => {
    const trackToRemove = playlist.tracks[index];
    const trackString = `${trackToRemove.artist}:${trackToRemove.title}`;

    onRemoveSong(trackString)
  };

  return (
    <div>
      <MDBCard
        id="playlistPanel"
        className="chat-widget-card"
        style={{ borderRadius: "15px",
          maxWidth: "500px"
         }}
      >
        <MDBCardHeader
          className="d-flex justify-content-between align-items-center p-3 bg-info text-white border-bottom-0"
          style={{
            borderTopLeftRadius: "15px",
            borderTopRightRadius: "15px",
          }}
        >
          <div>
            <p className="mb-0 fw-bold">Playlist - {playlist.name}</p>
          </div>
        </MDBCardHeader>

        <MDBCardBody>
          <div className="playlist-content">

            {!playlist || playlist.tracks.length === 0 ? (
              <p className="text-muted text-center">No songs in the playlist yet 🎧</p>
            ) : (
              <div className="playlist-tracks">
                {playlist.tracks.map((track, index) => (

                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
>
                    <div 
                      key={index} 
                      className="playlist-track" 
                    >
                      <p className="track-title">{track.title}</p>
                      <p className="track-artist">{track.artist}</p>
                    </div>

                    <button
                      type="button"
                      className="btn btn-link text-muted"
                      onClick={() => handleRemoveTrack(index)}
                    >
                      <MDBIcon fas size="2x" icon="xmark" />
                    </button>
                  </div>
                ))}
              </div>
            )}

          </div>
        </MDBCardBody>
        <MDBCardFooter className="text-muted d-flex justify-content-start align-items-center p-2">
          <form className="d-flex flex-grow-1" onSubmit={handleSubmit}>

            <input
              type="text"
              className="form-control form-control-lg"
              id="Add a song (e.g. Artist - Title)"
              value={songInput}
              onChange={(e) => setSongInput(e.target.value)}
                placeholder="Add a song (Artist:Title)"
            ></input>

            <button type="submit" className="btn btn-link text-muted">
              <MDBIcon fas size="2x" icon="plus" />
            </button>
          </form>
        </MDBCardFooter>
      </MDBCard>
    </div>


  );
}
