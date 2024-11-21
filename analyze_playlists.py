import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict, Counter

def load_playlist_data():
    outputs_dir = Path("outputs")
    all_playlists = []
    
    for model_dir in outputs_dir.iterdir():
        if model_dir.is_dir() and not model_dir.name == "error_logs":
            model_name = model_dir.name.replace('_', '/')
            for playlist_file in model_dir.glob("playlist_*.json"):
                try:
                    with open(playlist_file) as f:
                        playlist_data = json.load(f)
                        # Add model information to each song
                        if "songs" in playlist_data:
                            for song in playlist_data["songs"]:
                                song["model"] = model_name
                                all_playlists.append(song)
                except Exception as e:
                    print(f"Error loading {playlist_file}: {e}")
    
    return pd.DataFrame(all_playlists)

def get_song_frequencies(df):
    # Combine song and artist to create unique identifier
    df['song_id'] = df['song'] + ' - ' + df['artist']
    return df['song_id'].value_counts()

def get_model_top_songs(df):
    model_songs = defaultdict(Counter)
    for _, row in df.iterrows():
        song_id = f"{row['song']} - {row['artist']}"
        model_songs[row['model']][song_id] += 1
    return model_songs

def create_song_frequency_plot(song_frequencies):
    """Create a bar plot showing the most frequent songs."""
    # Convert the series to a dataframe
    df = song_frequencies.reset_index()
    df.columns = ['song_id', 'count']
    
    fig = px.bar(
        df.head(10),
        x='count',
        y='song_id',
        title='Most Frequently Selected Songs',
        labels={'song_id': 'Song', 'count': 'Times Selected'},
        template='plotly_dark'  # Use dark theme
    )
    
    # Update bar color to Spotify green
    fig.update_traces(marker_color='#1DB954')
    
    fig.update_layout(
        height=400,  # Shorter height since it's only 10 items
        yaxis={'autorange': 'reversed'},  # Reverse y-axis to show most frequent at top
        xaxis_title='Times Selected',
        yaxis_title='Song',
        margin=dict(l=20, r=20, t=40, b=20)  # Adjust margins
    )
    
    return fig.to_html(full_html=False)

def create_model_comparison_plot(df):
    """Create a scatter plot comparing model song selections."""
    model_song_counts = df.groupby(['model', 'song_id']).size().reset_index(name='count')
    
    fig = px.scatter(
        model_song_counts,
        x='model',
        y='song_id',
        size='count',
        title='Song Selection Patterns by Model',
        template='plotly_dark',  # Use dark theme
        color_discrete_sequence=['#1DB954'],  # Spotify green
        hover_data=['count']  # Show count in hover tooltip
    )
    
    fig.update_layout(
        height=1000,  # Taller to accommodate all songs
        xaxis_title='Model',
        yaxis_title='Song',
        showlegend=False,
        yaxis={'autorange': 'reversed'},  # Reverse y-axis for better readability
        yaxis_tickangle=0,  # Make song names horizontal
        margin=dict(l=20, r=20, t=40, b=20)  # Adjust margins
    )
    
    # Update marker style
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='#191414'),  # Dark border around points
            opacity=0.7  # Slight transparency
        )
    )
    
    return fig.to_html(full_html=False)

def create_model_diversity_plot(model_songs):
    """Create a bar plot showing model diversity."""
    # Calculate unique songs per model
    model_unique_songs = {model: len(set(songs)) for model, songs in model_songs.items()}
    
    # Sort models by number of unique songs
    sorted_models = dict(sorted(model_unique_songs.items(), key=lambda x: x[1], reverse=True))
    
    # Create bar plot
    fig = go.Figure(data=[
        go.Bar(
            x=list(sorted_models.keys()),
            y=list(sorted_models.values()),
            marker_color='#1DB954'  # Spotify green
        )
    ])
    
    fig.update_layout(
        title='Model Song Selection Diversity',
        xaxis_title='Model',
        yaxis_title='Number of Unique Songs',
        template='plotly_dark',
        height=500,  # Good height for bar chart
        margin=dict(l=20, r=20, t=40, b=20)  # Adjust margins
    )
    
    return fig.to_html(full_html=False)

def get_model_statistics(df):
    """Calculate statistics for each model."""
    from spotify_utils import get_track_info
    stats = []
    
    # Create song_id if it doesn't exist
    if 'song_id' not in df.columns:
        df['song_id'] = df['song'] + ' - ' + df['artist']
    
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        unique_songs = len(model_df['song_id'].unique())
        total_songs = len(model_df)
        
        # Get top songs with Spotify data
        top_songs = []
        for _, row in model_df.groupby(['song', 'artist'])['song'].count().reset_index(name='count').sort_values('count', ascending=False).head(5).iterrows():
            song_info = get_track_info(row['song'], row['artist'])
            top_songs.append({
                'song': row['song'],
                'artist': row['artist'],
                'count': row['count'],
                'spotify_url': song_info.get('spotify_url', ''),
                'image_url': song_info.get('image_url', '')
            })
        
        # Get top artists with Spotify data
        top_artists = []
        for _, row in model_df.groupby(['artist'])['artist'].count().reset_index(name='count').sort_values('count', ascending=False).head(5).iterrows():
            # Get artist image from their most played song
            artist_song = model_df[model_df['artist'] == row['artist']].iloc[0]
            song_info = get_track_info(artist_song['song'], row['artist'])
            top_artists.append({
                'artist': row['artist'],
                'count': row['count'],
                'spotify_url': song_info.get('spotify_url', ''),
                'image_url': song_info.get('image_url', '')
            })
        
        stats.append({
            'model': model,
            'unique_songs': unique_songs,
            'total_songs': total_songs,
            'diversity_ratio': round(unique_songs / total_songs, 2) if total_songs > 0 else 0,
            'top_songs': top_songs,
            'top_artists': top_artists
        })
    
    return pd.DataFrame(stats)
