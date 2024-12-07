import os
import json
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time

load_dotenv()

# Cache file path
CACHE_FILE = "spotify_cache.json"


# Load cache
def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# Save cache
def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


# Initialize cache
cache = load_cache()

# Initialize Spotify client
spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    )
)


def get_track_info(song_name, artist_name):
    """Search for a track and return its Spotify information."""
    search_key = f"{song_name} - {artist_name}"

    # Check cache first
    if search_key in cache:
        # If we have a valid Spotify URL in cache, use it
        if cache[search_key].get("spotify_url"):
            return cache[search_key]

    try:
        # Add delay to avoid rate limiting
        time.sleep(0.1)

        # Search for the track
        query = f"track:{song_name} artist:{artist_name}"
        results = spotify.search(q=query, type="track", limit=1)

        if results["tracks"]["items"]:
            track = results["tracks"]["items"][0]

            # Get artist genres
            artist_id = track["artists"][0]["id"]
            artist = spotify.artist(artist_id)
            genres = artist["genres"]

            # Get album genres
            album_id = track["album"]["id"]
            album = spotify.album(album_id)
            album_genres = album.get("genres", [])

            # Combine and deduplicate genres
            all_genres = list(set(genres + album_genres))

            track_info = {
                "image_url": (
                    track["album"]["images"][0]["url"]
                    if track["album"]["images"]
                    else None
                ),
                "spotify_url": track["external_urls"]["spotify"],
                "preview_url": track["preview_url"],
                "album_name": track["album"]["name"],
                "genres": all_genres,
                "genre": (
                    all_genres[0] if all_genres else "Unknown"
                ),  # Use first genre as primary
            }

            # Update cache
            cache[search_key] = track_info
            save_cache(cache)
            return track_info
    except Exception as e:
        pass

    # Default values for missing/error cases
    default_info = {
        "image_url": "https://place-hold.it/300x300/666/fff/000.png?text=No%20Image",
        "spotify_url": None,
        "preview_url": None,
        "album_name": "Unknown Album",
        "genres": [],
        "genre": "Unknown",
    }

    # Only cache if not already in cache
    if search_key not in cache:
        cache[search_key] = default_info
        save_cache(cache)
    return default_info


def enrich_playlist_data(playlist_data):
    """Add Spotify information to playlist data."""
    for song in playlist_data:
        spotify_info = get_track_info(song["song"], song["artist"])
        song.update(spotify_info)
    return playlist_data
