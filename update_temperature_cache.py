"""Update Spotify cache with songs from temperature study."""

from pathlib import Path
import json
from spotify_utils import get_track_info
import time


def update_cache():
    """Update cache with songs from temperature study outputs."""
    outputs_dir = Path("outputs")
    processed_songs = set()

    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Load existing cache if any
    cache_file = data_dir / "spotify_cache.json"
    if cache_file.exists():
        print("Loading existing cache...")
        with open(cache_file) as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} songs from cache")
    else:
        cache = {}
        print("Starting with empty cache")

    print("\nLooking for temperature study data...")
    for temp_dir in outputs_dir.glob("temperature_study_*"):
        if not temp_dir.is_dir():
            continue

        print(f"\nProcessing directory: {temp_dir}")
        for playlist_file in temp_dir.glob("playlist_*.json"):
            print(f"Processing file: {playlist_file}")
            try:
                with open(playlist_file) as f:
                    playlist_data = json.load(f)
                    if "songs" in playlist_data:
                        for song in playlist_data["songs"]:
                            song_key = f"{song['song']} - {song['artist']}"
                            if song_key not in processed_songs:
                                print(f"Getting info for: {song_key}")
                                info = get_track_info(song["song"], song["artist"])
                                if info.get("genres"):
                                    print(f"Found genres: {info['genres']}")
                                processed_songs.add(song_key)
                                cache[song_key] = info
                                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Error processing {playlist_file}: {e}")

    print(f"\nProcessed {len(processed_songs)} unique songs")
    print(f"Cache now contains {len(cache)} songs")

    # Save cache to data directory
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)
    print(f"Cache saved to {cache_file}")


if __name__ == "__main__":
    update_cache()
