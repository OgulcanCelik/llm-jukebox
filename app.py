from flask import Flask, render_template
import pandas as pd
from analyze_playlists import (
    load_playlist_data,
    get_song_frequencies,
    get_model_top_songs,
    create_song_frequency_plot,
    create_model_comparison_plot,
    create_model_diversity_plot,
    get_model_statistics
)
from spotify_utils import enrich_playlist_data
from genre_analysis import get_genre_statistics, create_genre_distribution_plot, create_genre_heatmap

app = Flask(__name__)

def generate_page_data():
    """Generate all the data needed for the page."""
    df = load_playlist_data()
    
    # Create song_id column
    df['song_id'] = df['song'] + ' - ' + df['artist']
    
    # Get total songs and models
    total_songs = len(df)
    total_models = df['model'].nunique()
    
    # Get model statistics
    model_stats = get_model_statistics(df)
    
    # Generate plots
    song_freq_plot = create_song_frequency_plot(get_song_frequencies(df))
    model_comparison_plot = create_model_comparison_plot(df)
    model_diversity_plot = create_model_diversity_plot(get_model_top_songs(df))
    
    # Get playlists with Spotify metadata
    playlists = {}
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        top_songs = []
        for song_id, count in model_df['song_id'].value_counts().head(10).items():
            song_row = model_df[model_df['song_id'] == song_id].iloc[0]
            top_songs.append({
                'song': song_row['song'],
                'artist': song_row['artist'],
                'count': count
            })
        playlists[model] = enrich_playlist_data(top_songs)
    
    # Get genre statistics and visualizations
    genre_data = get_genre_statistics(playlists)
    
    # Get the top genre
    top_genre = next(iter(genre_data['genre_stats']['top_genres']), 'N/A')
    
    return {
        'total_songs': total_songs,
        'total_models': total_models,
        'model_stats': model_stats.to_dict('records'),
        'song_freq_plot': song_freq_plot,
        'model_comparison_plot': model_comparison_plot,
        'model_diversity_plot': model_diversity_plot,
        'genre_distribution_plot': genre_data['genre_distribution_plot'],
        'genre_heatmap': genre_data['genre_heatmap'],
        'genre_stats': genre_data['genre_stats'],
        'top_genre': top_genre,
        'playlists': playlists
    }

@app.route('/')
def index():
    """Render the index page with all data."""
    return render_template('index.html', **generate_page_data())

def create_static_site(dist_dir):
    """Generate a static version of the site."""
    # Get all the data
    data = generate_page_data()
    
    # Render the template
    html_content = render_template('index.html', **data)
    
    # Write the HTML file
    with open(os.path.join(dist_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Copy static assets
    static_dir = os.path.join(app.root_path, 'static')
    if os.path.exists(static_dir):
        shutil.copytree(static_dir, os.path.join(dist_dir, 'static'))

if __name__ == '__main__':
    app.run(debug=True)
