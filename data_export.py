import os
import json
import pandas as pd
from pathlib import Path
from genre_analysis import load_genre_cache

def export_data(output_dir="data_exports"):
    """Export all data in a single comprehensive CSV."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Load genre cache
    genre_cache = load_genre_cache()
    
    # Collect all song choices with timestamps
    all_songs = []
    outputs_dir = Path("outputs")
    
    for model_dir in outputs_dir.iterdir():
        if model_dir.is_dir() and not model_dir.name == "error_logs":
            model_name = model_dir.name.replace('_', '/')
            for playlist_file in model_dir.glob("playlist_*.json"):
                try:
                    with open(playlist_file) as f:
                        playlist_data = json.load(f)
                        if "songs" in playlist_data:
                            # Extract timestamp from filename
                            # Format: playlist_run1_20241121_161159.json
                            timestamp = playlist_file.stem.split('_', 2)[2]  # Get '20241121_161159'
                            timestamp = timestamp.replace('_', '')  # Convert to '20241121161159'
                            
                            for song in playlist_data["songs"]:
                                # Get genres for the artist
                                artist_genres = genre_cache.get(song["artist"], [])
                                # Join multiple genres with semicolon
                                genres = "; ".join(artist_genres) if artist_genres else "Unknown"
                                
                                all_songs.append({
                                    "model": model_name,
                                    "timestamp": timestamp,
                                    "song": song["song"],
                                    "artist": song["artist"],
                                    "genres": genres
                                })
                except Exception as e:
                    print(f"Error loading {playlist_file}: {e}")
    
    # Convert to DataFrame and export
    df = pd.DataFrame(all_songs)
    
    # Sort by model and timestamp
    df = df.sort_values(['model', 'timestamp'])
    
    # Export only the CSV
    df.to_csv(f"{output_dir}/llm_music_choices.csv", index=False)

if __name__ == "__main__":
    export_data()
