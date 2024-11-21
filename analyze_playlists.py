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

def create_song_frequency_plot(song_freq):
    fig = px.bar(
        x=song_freq.values[:20],
        y=song_freq.index[:20],
        orientation='h',
        title='Top 20 Most Frequently Selected Songs Across All Models',
        labels={'x': 'Frequency', 'y': 'Song - Artist'}
    )
    return fig.to_html(full_html=False)

def create_model_comparison_plot(df):
    model_song_counts = df.groupby(['model', 'song_id']).size().reset_index(name='count')
    fig = px.scatter(
        model_song_counts,
        x='model',
        y='count',
        size='count',
        hover_data=['song_id'],
        title='Song Selection Patterns by Model',
        labels={'model': 'Model', 'count': 'Times Selected', 'song_id': 'Song'}
    )
    return fig.to_html(full_html=False)

def create_model_diversity_plot(model_songs):
    diversity_data = []
    for model, songs in model_songs.items():
        unique_songs = len(songs)
        total_songs = sum(songs.values())
        diversity_data.append({
            'model': model,
            'unique_songs': unique_songs,
            'total_songs': total_songs,
            'diversity_ratio': unique_songs / total_songs if total_songs > 0 else 0
        })
    
    df_diversity = pd.DataFrame(diversity_data)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Unique Songs',
        x=df_diversity['model'],
        y=df_diversity['unique_songs'],
        marker_color='lightblue'
    ))
    fig.add_trace(go.Bar(
        name='Total Songs',
        x=df_diversity['model'],
        y=df_diversity['total_songs'],
        marker_color='darkblue'
    ))
    fig.update_layout(
        title='Model Song Selection Diversity',
        barmode='group'
    )
    return fig.to_html(full_html=False)

def get_model_statistics(df):
    stats = []
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        unique_songs = len(model_df['song_id'].unique())
        total_songs = len(model_df)
        most_common = model_df['song_id'].value_counts().head(1)
        stats.append({
            'model': model,
            'unique_songs': unique_songs,
            'total_songs': total_songs,
            'diversity_ratio': unique_songs / total_songs if total_songs > 0 else 0,
            'most_common_song': most_common.index[0] if not most_common.empty else 'N/A',
            'most_common_count': most_common.values[0] if not most_common.empty else 0
        })
    return pd.DataFrame(stats)
