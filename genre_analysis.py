import os
import json
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from spotify_utils import spotify

# Cache file path
GENRE_CACHE_FILE = "genre_cache.json"


def load_genre_cache():
    """Load genre cache from file."""
    try:
        with open(GENRE_CACHE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_genre_cache(cache):
    """Save genre cache to file."""
    with open(GENRE_CACHE_FILE, "w") as f:
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
        results = spotify.search(q=artist_name, type="artist", limit=1)
        if results["artists"]["items"]:
            genres = results["artists"]["items"][0]["genres"]
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
            artist_name = song["artist"]
            genres = get_artist_genres(artist_name)

            # Add each genre as a separate row for better visualization
            for genre in genres:
                genre_data.append(
                    {
                        "model": model_name,
                        "artist": artist_name,
                        "song": song["song"],
                        "genre": genre,
                    }
                )

    return pd.DataFrame(genre_data)


def create_genre_distribution_plot(genre_df):
    """Create a stacked bar chart showing genre distribution per model."""
    # Normalize genres
    genre_df = genre_df.copy()
    genre_df["normalized_genre"] = genre_df["genre"].apply(normalize_genre)
    
    # Count genres per model, using normalized genres
    genre_counts = genre_df.groupby(["model", "normalized_genre"]).size().reset_index(name="count")
    
    # Get top 10 genres by total count across all models
    top_genres = genre_df["normalized_genre"].value_counts().head(10).index
    genre_counts = genre_counts[genre_counts["normalized_genre"].isin(top_genres)]
    
    # Calculate percentages
    total_per_model = genre_counts.groupby("model")["count"].sum()
    genre_counts["percentage"] = genre_counts.apply(
        lambda x: (x["count"] / total_per_model[x["model"]]) * 100, axis=1
    )
    
    # Create stacked bar chart
    fig = px.bar(
        genre_counts,
        x="model",
        y="percentage",
        color="normalized_genre",
        title="Genre Distribution by Model (Top 10 Genres)",
        labels={
            "percentage": "Percentage",
            "model": "Model",
            "normalized_genre": "Genre"
        },
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    
    # Update layout for better visibility
    fig.update_layout(
        barmode="stack",
        showlegend=True,
        legend_title_text="Genre",
        xaxis_title="Model",
        yaxis_title="Percentage of Songs",
        height=600,
        width=1000,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_x=0.5,
        font_size=12,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(255,255,255,0.3)"
        ),
        margin=dict(r=150)  # Add right margin for legend
    )
    
    # Update bars
    fig.update_traces(
        marker_line_color='rgba(255,255,255,0.3)',
        marker_line_width=1,
        opacity=0.8
    )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_genre_heatmap(genre_df):
    """Create a heatmap showing genre preferences across models."""
    # Count genres per model
    genre_matrix = pd.crosstab(genre_df["model"], genre_df["genre"])

    # Convert to percentages
    genre_matrix_pct = genre_matrix.div(genre_matrix.sum(axis=1), axis=0) * 100

    # Create heatmap with a green-focused colorscale
    custom_colorscale = [
        [0, "#191414"],  # Dark background color
        [0.5, "#535353"],  # Mid-gray
        [1, "#1DB954"],  # Spotify green
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=genre_matrix_pct.values,
            x=genre_matrix_pct.columns,
            y=genre_matrix_pct.index,
            colorscale=custom_colorscale,
            colorbar=dict(title="Percentage"),
        )
    )

    fig.update_layout(
        title="Genre Preference Heatmap",
        xaxis_title="Genre",
        yaxis_title="Model",
        template="plotly_dark",
        height=600,
        xaxis={"tickangle": 45},
    )

    return fig.to_html(full_html=False)


def normalize_genre(genre):
    """Normalize genres to main categories."""
    # Convert to lowercase for consistent matching
    genre = genre.lower()
    
    # Genre mapping dictionary
    genre_mapping = {
        # Rock variants
        'alt-rock': 'rock',
        'alternative rock': 'rock',
        'hard rock': 'rock',
        'indie rock': 'rock',
        'modern rock': 'rock',
        'post-rock': 'rock',
        'prog-rock': 'rock',
        'progressive rock': 'rock',
        'punk rock': 'rock',
        'rock-n-roll': 'rock',
        'soft rock': 'rock',
        'garage rock': 'rock',
        'grunge': 'rock',
        'psychedelic rock': 'rock',
        'classic rock': 'rock',
        
        # Pop variants
        'art pop': 'pop',
        'dance pop': 'pop',
        'electropop': 'pop',
        'indie pop': 'pop',
        'k-pop': 'pop',
        'synth-pop': 'pop',
        'pop rock': 'pop',
        'power pop': 'pop',
        'dream pop': 'pop',
        'chamber pop': 'pop',
        'baroque pop': 'pop',
        
        # Electronic variants
        'ambient': 'electronic',
        'downtempo': 'electronic',
        'drum and bass': 'electronic',
        'dubstep': 'electronic',
        'edm': 'electronic',
        'electronica': 'electronic',
        'house': 'electronic',
        'idm': 'electronic',
        'techno': 'electronic',
        'trance': 'electronic',
        'trip-hop': 'electronic',
        'synthwave': 'electronic',
        'electro': 'electronic',
        
        # Hip-hop variants
        'rap': 'hip-hop',
        'trap': 'hip-hop',
        'conscious hip hop': 'hip-hop',
        'alternative hip hop': 'hip-hop',
        'underground hip hop': 'hip-hop',
        'gangsta rap': 'hip-hop',
        'old school hip hop': 'hip-hop',
        
        # R&B variants
        'contemporary r&b': 'r&b',
        'neo soul': 'r&b',
        'soul': 'r&b',
        'funk': 'r&b',
        'motown': 'r&b',
        'rhythm and blues': 'r&b',
        
        # Jazz variants
        'acid jazz': 'jazz',
        'bebop': 'jazz',
        'big band': 'jazz',
        'cool jazz': 'jazz',
        'fusion': 'jazz',
        'latin jazz': 'jazz',
        'smooth jazz': 'jazz',
        'swing': 'jazz',
        'vocal jazz': 'jazz',
        'nu jazz': 'jazz',
        
        # Folk variants
        'indie folk': 'folk',
        'folk rock': 'folk',
        'contemporary folk': 'folk',
        'traditional folk': 'folk',
        'americana': 'folk',
        'bluegrass': 'folk',
        
        # Metal variants
        'black metal': 'metal',
        'death metal': 'metal',
        'doom metal': 'metal',
        'heavy metal': 'metal',
        'power metal': 'metal',
        'progressive metal': 'metal',
        'thrash metal': 'metal',
        'nu metal': 'metal',
        
        # Classical variants
        'baroque': 'classical',
        'chamber music': 'classical',
        'choral': 'classical',
        'contemporary classical': 'classical',
        'modern classical': 'classical',
        'opera': 'classical',
        'orchestral': 'classical',
        'romantic': 'classical',
        'symphony': 'classical',
        
        # Country variants
        'alternative country': 'country',
        'contemporary country': 'country',
        'country rock': 'country',
        'outlaw country': 'country',
        'traditional country': 'country',
        
        # Blues variants
        'blues rock': 'blues',
        'chicago blues': 'blues',
        'delta blues': 'blues',
        'electric blues': 'blues',
        'modern blues': 'blues',
        
        # Reggae variants
        'dub': 'reggae',
        'roots reggae': 'reggae',
        'ska': 'reggae',
        'dancehall': 'reggae',
    }
    
    # Check direct mapping
    if genre in genre_mapping:
        return genre_mapping[genre]
    
    # Check if genre contains any of the main categories
    main_genres = {
        'rock', 'pop', 'electronic', 'hip-hop', 'r&b', 'jazz',
        'folk', 'metal', 'classical', 'country', 'blues', 'reggae'
    }
    
    for main_genre in main_genres:
        if main_genre in genre:
            return main_genre
    
    # Check for partial matches in mapping
    for mapped_genre, main_genre in genre_mapping.items():
        if mapped_genre in genre:
            return main_genre
    
    return genre  # Return original if no mapping found


def create_chord_diagram(genre_df):
    """Create a chord diagram showing genre relationships between models."""
    import plotly.graph_objects as go
    import numpy as np
    
    # Normalize genres
    genre_df["normalized_genre"] = genre_df["genre"].apply(normalize_genre)
    
    # Get unique models and genres
    models = genre_df["model"].unique()
    genres = genre_df["normalized_genre"].value_counts().head(10).index  # Top 10 genres
    
    # Create a matrix of connections
    matrix = np.zeros((len(models), len(genres)))
    
    # Fill the matrix with counts
    for i, model in enumerate(models):
        model_genres = genre_df[genre_df["model"] == model]["normalized_genre"].value_counts()
        for j, genre in enumerate(genres):
            if genre in model_genres:
                matrix[i][j] = model_genres[genre]
    
    # Define vibrant colors for models
    model_colors = [
        (255, 107, 107),  # Coral Red
        (78, 205, 196),   # Turquoise
        (69, 183, 209),   # Sky Blue
        (150, 206, 180),  # Sage Green
        (255, 238, 173),  # Cream
        (212, 165, 165),  # Dusty Rose
        (155, 89, 182),   # Purple
        (52, 152, 219),   # Blue
        (230, 126, 34),   # Orange
        (39, 174, 96)     # Green
    ]
    
    # Convert RGB tuples to hex for nodes
    model_hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in model_colors]
    
    # Ensure we have enough colors
    while len(model_hex_colors) < len(models):
        model_hex_colors.extend(model_hex_colors)
    model_hex_colors = model_hex_colors[:len(models)]
    
    # Genre colors will be grayscale
    genre_colors = ["#" + hex(i)[2:].zfill(6) for i in np.linspace(0x404040, 0x808080, len(genres)).astype(int)]
    
    # Combine colors for nodes
    node_colors = model_hex_colors + genre_colors
    
    # Create source-target pairs and values
    source = []
    target = []
    values = []
    link_colors = []
    
    for i in range(len(models)):
        for j in range(len(genres)):
            if matrix[i][j] > 0:  # Only add connections that exist
                source.append(i)
                target.append(j + len(models))
                values.append(matrix[i][j])
                r, g, b = model_colors[i]
                link_colors.append(f"rgba({r},{g},{b},0.4)")  # Using rgba for transparency
    
    # Create the chord diagram
    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",  # Makes it more circular-like
                node=dict(
                    pad=20,
                    thickness=20,
                    line=dict(color="white", width=0.5),
                    label=list(models) + list(genres),
                    color=node_colors,
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=values,
                    color=link_colors,
                ),
            )
        ]
    )
    
    # Update layout
    fig.update_layout(
        title_text="Model-Genre Relationships",
        font_size=12,
        template="plotly_dark",
        height=800,
        width=1000,
        title_x=0.5,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def get_genre_statistics(playlists):
    """Generate genre statistics and visualizations for the playlists."""
    # Process the data
    genre_df = load_and_process_genres(playlists)

    # Generate visualizations
    distribution_plot = create_genre_distribution_plot(genre_df)
    heatmap_plot = create_genre_heatmap(genre_df)
    chord_diagram_plot = create_chord_diagram(genre_df)

    # Calculate some basic statistics
    genre_stats = {
        "total_genres": len(genre_df["genre"].unique()),
        "genres_per_model": genre_df.groupby("model")["genre"].nunique().to_dict(),
        "top_genres": genre_df["genre"].value_counts().head(5).to_dict(),
    }

    return {
        "genre_distribution_plot": distribution_plot,
        "genre_heatmap": heatmap_plot,
        "genre_chord_diagram": chord_diagram_plot,
        "genre_stats": genre_stats,
    }
