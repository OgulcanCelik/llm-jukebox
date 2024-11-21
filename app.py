from flask import Flask, render_template
import os
import shutil
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

app = Flask(__name__)

def generate_page_data():
    """Generate all the data needed for the page."""
    # Load and process data
    df = load_playlist_data()
    song_frequencies = get_song_frequencies(df)
    model_songs = get_model_top_songs(df)
    model_stats = get_model_statistics(df)
    
    # Create visualizations
    song_freq_plot = create_song_frequency_plot(song_frequencies)
    model_comparison_plot = create_model_comparison_plot(df)
    model_diversity_plot = create_model_diversity_plot(model_songs)
    
    # Get top songs per model and enrich with Spotify data
    playlists = {}
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        top_songs = []
        for song_id, count in model_df['song_id'].value_counts().head(10).items():
            song_name, artist_name = song_id.split(' - ', 1)
            top_songs.append({
                'song': song_name,
                'artist': artist_name,
                'count': count
            })
        playlists[model] = enrich_playlist_data(top_songs)
    
    return {
        'song_freq_plot': song_freq_plot,
        'model_comparison_plot': model_comparison_plot,
        'model_diversity_plot': model_diversity_plot,
        'model_stats': model_stats.to_dict('records'),
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
