import os
import json
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from spotify_utils import spotify

# Cache file path
GENRE_CACHE_FILE = 'genre_cache.json'

def load_genre_cache():
    """Load genre cache from file."""
    try:
        with open(GENRE_CACHE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_genre_cache(cache):
    """Save genre cache to file."""
    with open(GENRE_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

# Initialize cache
genre_cache = load_genre_cache()

def get_artist_genres(artist_name):
    """Get genres for an artist using Spotify API with caching."""
    # Check cache first
    if artist_name in genre_cache:
        return genre_cache[artist_name]
    
    try:
        # Search for the artist
        results = spotify.search(q=artist_name, type='artist', limit=1)
        if results['artists']['items']:
            genres = results['artists']['items'][0]['genres']
            # Cache the result
            genre_cache[artist_name] = genres
            save_genre_cache(genre_cache)
            return genres
        return []
    except Exception as e:
        print(f"Error getting genres for {artist_name}: {e}")
        # Cache empty result to avoid repeated failed requests
        genre_cache[artist_name] = []
        save_genre_cache(genre_cache)
        return []

def load_and_process_genres(playlist_data):
    """Load playlist data and get genres for each song."""
    genre_data = []
    
    for model_name, songs in playlist_data.items():
        for song in songs:
            artist_name = song['artist']
            genres = get_artist_genres(artist_name)
            
            # Add each genre as a separate row for better visualization
            for genre in genres:
                genre_data.append({
                    'model': model_name,
                    'artist': artist_name,
                    'song': song['song'],
                    'genre': genre
                })
    
    return pd.DataFrame(genre_data)

def create_genre_distribution_plot(genre_df):
    """Create a stacked bar chart showing genre distribution per model."""
    # Count genres per model
    genre_counts = genre_df.groupby(['model', 'genre']).size().reset_index(name='count')
    
    # Calculate percentages
    total_per_model = genre_counts.groupby('model')['count'].sum()
    genre_counts['percentage'] = genre_counts.apply(
        lambda x: (x['count'] / total_per_model[x['model']]) * 100, 
        axis=1
    )
    
    # Create stacked bar chart
    fig = px.bar(
        genre_counts,
        x='model',
        y='percentage',
        color='genre',
        title='Genre Distribution by Model',
        labels={'percentage': 'Percentage', 'model': 'Model', 'genre': 'Genre'},
        template='plotly_dark',
        color_discrete_sequence=px.colors.qualitative.Set3  # Use a color palette that works well with dark theme
    )
    
    fig.update_layout(
        barmode='stack',
        showlegend=True,
        legend_title_text='Genre',
        xaxis_title='Model',
        yaxis_title='Percentage of Songs',
        height=600
    )
    
    return fig.to_html(full_html=False)

def create_genre_heatmap(genre_df):
    """Create a heatmap showing genre preferences across models."""
    # Count genres per model
    genre_matrix = pd.crosstab(genre_df['model'], genre_df['genre'])
    
    # Convert to percentages
    genre_matrix_pct = genre_matrix.div(genre_matrix.sum(axis=1), axis=0) * 100
    
    # Create heatmap with a green-focused colorscale
    custom_colorscale = [
        [0, '#191414'],  # Dark background color
        [0.5, '#535353'],  # Mid-gray
        [1, '#1DB954']  # Spotify green
    ]
    
    fig = go.Figure(data=go.Heatmap(
        z=genre_matrix_pct.values,
        x=genre_matrix_pct.columns,
        y=genre_matrix_pct.index,
        colorscale=custom_colorscale,
        colorbar=dict(title='Percentage')
    ))
    
    fig.update_layout(
        title='Genre Preference Heatmap',
        xaxis_title='Genre',
        yaxis_title='Model',
        template='plotly_dark',
        height=600,
        xaxis={'tickangle': 45}
    )
    
    return fig.to_html(full_html=False)

def get_genre_statistics(playlists):
    """Generate genre statistics and visualizations for the playlists."""
    # Process the data
    genre_df = load_and_process_genres(playlists)
    
    # Generate visualizations
    distribution_plot = create_genre_distribution_plot(genre_df)
    heatmap_plot = create_genre_heatmap(genre_df)
    
    # Calculate some basic statistics
    genre_stats = {
        'total_genres': len(genre_df['genre'].unique()),
        'genres_per_model': genre_df.groupby('model')['genre'].nunique().to_dict(),
        'top_genres': genre_df['genre'].value_counts().head(5).to_dict()
    }
    
    return {
        'genre_distribution_plot': distribution_plot,
        'genre_heatmap': heatmap_plot,
        'genre_stats': genre_stats
    }
