from flask import Flask, render_template, send_from_directory
import pandas as pd
from analyze_playlists import (
    load_playlist_data,
    get_song_frequencies,
    get_model_top_songs,
    create_song_frequency_plot,
    create_model_comparison_plot,
    create_model_diversity_plot,
    get_model_statistics,
)
from spotify_utils import enrich_playlist_data
from genre_analysis import (
    get_genre_statistics,
    create_genre_distribution_plot,
    create_genre_heatmap,
)
from data_export import export_data
import os
import shutil
from pathlib import Path
import plotly.express as px

app = Flask(__name__)

# Export data on startup
export_data()


def get_experiment_stats():
    """Get statistics about the experiment."""
    outputs_dir = Path("outputs")
    stats = {
        "total_runs": 0,
        "total_songs": 0,
        "models": [],
        "runs_per_model": {},
        "songs_per_run": 10,  # We always ask for 10 songs
    }
    
    # Count files per model directory
    for model_dir in outputs_dir.iterdir():
        if model_dir.is_dir() and not model_dir.name == "error_logs":
            model_name = model_dir.name.replace('_', '/')
            playlist_files = list(model_dir.glob("playlist_*.json"))
            num_runs = len(playlist_files)
            
            stats["models"].append(model_name)
            stats["runs_per_model"][model_name] = num_runs
            stats["total_runs"] += num_runs
            stats["total_songs"] += num_runs * stats["songs_per_run"]
    
    return stats


def generate_page_data():
    """Generate all data needed for the page."""
    # Get experiment stats
    experiment_stats = get_experiment_stats()

    df = load_playlist_data()

    # Create song_id column
    df["song_id"] = df["song"] + " - " + df["artist"]

    # Get total songs and models
    total_songs = len(df)
    total_models = df["model"].nunique()

    # Get model statistics
    model_stats = get_model_statistics(df)

    # Get song frequency data for plot
    song_counts = df.groupby(['song', 'artist']).size().reset_index(name='count')
    song_counts['song_artist'] = song_counts['song'] + ' - ' + song_counts['artist']
    song_counts = song_counts.sort_values('count', ascending=False)
    
    # Get artist frequency data for plot
    artist_counts = df['artist'].value_counts().reset_index()
    artist_counts.columns = ['artist', 'count']
    
    # Create frequency plots
    song_freq_plot = px.bar(
        song_counts.head(10),
        x='count',
        y='song_artist',
        orientation='h',
        title='Most Frequent Songs Across All Models',
        labels={'count': 'Times Selected', 'song_artist': 'Song'},
        template='plotly_dark',  # Use dark theme
        height=400,
    )
    song_freq_plot.update_layout(
        yaxis={'autorange': 'reversed'},  # Reverse y-axis to show most frequent at top
        xaxis_title='Times Selected',
        yaxis_title=None,
        margin=dict(l=20, r=20, t=40, b=20),  # Adjust margins
        title_x=0.5,
    )
    song_freq_plot.update_traces(
        marker_color='#1DB954',  # Spotify green
        marker=dict(
            line=dict(width=1, color='#191414'),  # Dark border around bars
            opacity=0.9
        )
    )
    
    artist_freq_plot = px.bar(
        artist_counts.head(10),
        x='count',
        y='artist',
        orientation='h',
        title='Most Frequent Artists Across All Models',
        labels={'count': 'Times Selected', 'artist': 'Artist'},
        template='plotly_dark',  # Use dark theme
        height=400,
    )
    artist_freq_plot.update_layout(
        yaxis={'autorange': 'reversed'},  # Reverse y-axis to show most frequent at top
        xaxis_title='Times Selected',
        yaxis_title=None,
        margin=dict(l=20, r=20, t=40, b=20),  # Adjust margins
        title_x=0.5,
    )
    artist_freq_plot.update_traces(
        marker_color='#1DB954',  # Spotify green
        marker=dict(
            line=dict(width=1, color='#191414'),  # Dark border around bars
            opacity=0.9
        )
    )
    
    # Convert plots to HTML
    song_freq_plot = song_freq_plot.to_html(full_html=False, include_plotlyjs=False)
    artist_freq_plot = artist_freq_plot.to_html(full_html=False, include_plotlyjs=False)
    
    # Get other plots (these are already HTML strings)
    model_comparison_plot = create_model_comparison_plot(df)
    if isinstance(model_comparison_plot, str):
        model_comparison_plot_html = model_comparison_plot
    else:
        model_comparison_plot_html = model_comparison_plot.to_html(full_html=False, include_plotlyjs=False)
        
    model_diversity_plot = create_model_diversity_plot(get_model_top_songs(df))
    if isinstance(model_diversity_plot, str):
        model_diversity_plot_html = model_diversity_plot
    else:
        model_diversity_plot_html = model_diversity_plot.to_html(full_html=False, include_plotlyjs=False)

    # Get playlists with Spotify metadata
    playlists = {}
    for model in df["model"].unique():
        model_df = df[df["model"] == model]
        top_songs = []
        for song_id, count in model_df["song_id"].value_counts().head(10).items():
            song_row = model_df[model_df["song_id"] == song_id].iloc[0]
            top_songs.append(
                {"song": song_row["song"], "artist": song_row["artist"], "count": count}
            )
        playlists[model] = enrich_playlist_data(top_songs)

    # Get genre statistics and plots
    genre_analysis = get_genre_statistics(playlists)
    
    return {
        'playlists': playlists,
        'genre_distribution_plot': genre_analysis['genre_distribution_plot'],
        'genre_heatmap': genre_analysis['genre_heatmap'],
        'genre_chord_diagram': genre_analysis['genre_chord_diagram'],
        'genre_stats': genre_analysis['genre_stats'],
        'experiment_stats': experiment_stats,
        'total_songs': total_songs,
        'total_models': total_models,
        'model_stats': model_stats.to_dict("records"),
        'song_freq_plot': song_freq_plot,
        'artist_freq_plot': artist_freq_plot,
        'model_comparison_plot': model_comparison_plot_html,
        'model_diversity_plot': model_diversity_plot_html
    }


@app.route("/")
def index():
    data = generate_page_data()
    return render_template('index.html', **data)


@app.route("/data_exports/<path:filename>")
def get_data(filename):
    """Serve files from the data_exports directory."""
    return send_from_directory("data_exports", filename)


def create_static_site(dist_dir):
    """Generate a static version of the site."""
    import os
    import shutil
    
    # Create dist directory if it doesn't exist
    os.makedirs(dist_dir, exist_ok=True)
    
    # Create data_exports directory inside dist
    data_exports_dir = os.path.join(dist_dir, 'data_exports')
    os.makedirs(data_exports_dir, exist_ok=True)
    
    # Get all the data
    data = generate_page_data()

    # Render the template with the data
    with app.app_context():
        html_content = render_template('index.html', **data)

    # Write the HTML file
    with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    # Copy static assets
    static_dir = os.path.join(app.root_path, "static")
    if os.path.exists(static_dir):
        shutil.copytree(static_dir, os.path.join(dist_dir, "static"), dirs_exist_ok=True)
    
    # Copy data exports
    data_dir = os.path.join(app.root_path, "data_exports")
    if os.path.exists(data_dir):
        shutil.copytree(data_dir, os.path.join(dist_dir, "data_exports"), dirs_exist_ok=True)


if __name__ == "__main__":
    app.run(debug=True)
