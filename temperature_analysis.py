import json
from pathlib import Path
import pandas as pd
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
from genre_analysis import normalize_genre
from collections import Counter


def load_temperature_data():
    """Load data from temperature study outputs."""
    outputs_dir = Path("outputs")
    data = defaultdict(lambda: defaultdict(list))

    print(f"Looking for temperature study data in: {outputs_dir}")

    # Load cached Spotify data
    spotify_cache_file = Path("data/spotify_cache.json")
    if spotify_cache_file.exists():
        print("Loading Spotify cache...")
        with open(spotify_cache_file) as f:
            spotify_cache = json.load(f)
    else:
        print("No Spotify cache found!")
        spotify_cache = {}

    for temp_dir in outputs_dir.glob("temperature_study_*"):
        if not temp_dir.is_dir():
            continue

        print(f"Found temperature directory: {temp_dir}")

        # Extract temperature from directory name
        temp = float(temp_dir.name.split("_temp_")[1])
        print(f"Temperature value: {temp}")

        for playlist_file in temp_dir.glob("playlist_*.json"):
            # Extract model name from filename
            model_name = (
                playlist_file.name.split("playlist_")[1]
                .split("_run")[0]
                .replace("_", "/")
            )
            print(f"Processing file for model {model_name}: {playlist_file}")

            try:
                with open(playlist_file) as f:
                    playlist_data = json.load(f)
                    if "songs" in playlist_data:
                        for song in playlist_data["songs"]:
                            # Add temperature and model info
                            song["temperature"] = temp
                            song["model"] = model_name

                            # Get genre from Spotify cache
                            song_key = f"{song['song']} - {song['artist']}"
                            if song_key in spotify_cache:
                                song["genre"] = spotify_cache[song_key].get(
                                    "genre", "Unknown"
                                )
                                song["genres"] = spotify_cache[song_key].get(
                                    "genres", []
                                )
                            else:
                                song["genre"] = "Unknown"
                                song["genres"] = []

                            data[model_name][temp].append(song)
            except Exception as e:
                print(f"Error loading {playlist_file}: {e}")

    print("\nLoaded data summary:")
    for model, temp_data in data.items():
        for temp, songs in temp_data.items():
            print(f"Model: {model}, Temperature: {temp}, Songs: {len(songs)}")

    return data


def calculate_model_stats(data):
    """Calculate statistics for each model at different temperatures."""
    stats = {}

    for model, temp_data in data.items():
        stats[model] = {
            "low_temp": analyze_temperature_data(temp_data[0.1]),
            "high_temp": analyze_temperature_data(temp_data[0.8]),
        }

    return stats


def analyze_temperature_data(songs):
    """Analyze song data for a specific temperature."""
    # Count unique songs and their occurrences
    song_counts = Counter(f"{song['song']} - {song['artist']}" for song in songs)
    unique_songs = len(song_counts)

    # Count unique genres (excluding Unknown)
    all_genres = []
    for song in songs:
        if song.get("genres"):
            all_genres.extend(song["genres"])
        elif song.get("genre") and song["genre"] != "Unknown":
            all_genres.append(song["genre"])
    unique_genres = len(set(all_genres))

    # Calculate repetition rate (percentage of songs that appear more than once)
    repeated_songs = sum(1 for count in song_counts.values() if count > 1)
    repetition_rate = (repeated_songs / unique_songs * 100) if unique_songs > 0 else 0

    return {
        "unique_songs": unique_songs,
        "unique_genres": unique_genres,
        "repetition_rate": repetition_rate,
    }


def create_diversity_plot(data):
    """Create a plot comparing diversity metrics across temperatures."""
    plot_data = []

    print("\nCreating diversity plot:")
    for model, temp_data in data.items():
        print(f"\nModel: {model}")
        for temp, songs in temp_data.items():
            stats = analyze_temperature_data(songs)
            print(f"Temperature {temp}: {stats}")
            plot_data.append(
                {
                    "model": model,
                    "temperature": temp,
                    "unique_songs": stats["unique_songs"],
                    "unique_genres": stats["unique_genres"],
                    "repetition_rate": stats["repetition_rate"],
                }
            )

    df = pd.DataFrame(plot_data)
    print("\nDiversity plot data:")
    print(df)

    fig = go.Figure()

    metrics = {
        "unique_songs": "Unique Songs",
        "unique_genres": "Unique Genres",
        "repetition_rate": "Repetition Rate (%)",
    }

    colors = px.colors.qualitative.Set3

    for i, (metric, label) in enumerate(metrics.items()):
        fig.add_trace(
            go.Bar(
                name=label,
                x=[
                    f"{row['model']}\n(T={row['temperature']})"
                    for _, row in df.iterrows()
                ],
                y=df[metric],
                text=df[metric].round(2),
                textposition="auto",
                marker_color=colors[i],
                hovertemplate="%{x}<br>"
                + f"{label}: "
                + "%{y:.1f}<br>"
                + "<extra></extra>",
            )
        )

    fig.update_layout(
        title="Diversity Metrics by Model and Temperature",
        xaxis_title="Model and Temperature",
        yaxis_title="Value",
        barmode="group",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.2)", borderwidth=1
        ),
        margin=dict(t=50, l=50, r=50, b=100),
        height=600,  # Explicit height
        width=1000,  # Explicit width
    )

    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)

    return fig


def create_genre_distribution_plot(data):
    """Create a plot comparing genre distributions across temperatures."""
    plot_data = []

    for model, temp_data in data.items():
        for temp, songs in temp_data.items():
            # Get all genres (a song can have multiple genres)
            all_genres = []
            for song in songs:
                if song.get("genres"):
                    all_genres.extend(song["genres"])
                elif song.get("genre") and song["genre"] != "Unknown":
                    all_genres.append(song["genre"])

            genre_counts = Counter(all_genres)
            total_genres = sum(genre_counts.values())

            # Calculate percentages for top 10 genres
            if total_genres > 0:  # Only add data if we have genres
                for genre, count in genre_counts.most_common(10):
                    plot_data.append(
                        {
                            "model": model,
                            "temperature": temp,
                            "genre": genre,
                            "percentage": (count / total_genres) * 100,
                        }
                    )

    df = pd.DataFrame(plot_data)

    # Create empty plot if no data
    fig = go.Figure()

    if not df.empty:
        for model in df["model"].unique():
            model_data = df[df["model"] == model]

            for temp in model_data["temperature"].unique():
                temp_data = model_data[model_data["temperature"] == temp]

                fig.add_trace(
                    go.Bar(
                        name=f"{model} (T={temp})",
                        x=temp_data["genre"],
                        y=temp_data["percentage"],
                        text=temp_data["percentage"].round(1),
                        textposition="auto",
                        hovertemplate="%{x}<br>"
                        + "Percentage: %{y:.1f}%<br>"
                        + "<extra></extra>",
                    )
                )
    else:
        # Add placeholder text if no genre data
        fig.add_annotation(
            text="No genre data available.<br>Please run update_temperature_cache.py to fetch genre information.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="white"),
        )

    fig.update_layout(
        title="Genre Distribution by Model and Temperature",
        xaxis_title="Genre",
        yaxis_title="Percentage (%)",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.2)", borderwidth=1
        ),
        margin=dict(t=50, l=50, r=50, b=100),
        height=600,
        width=1000,
        barmode="group",
    )

    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)

    return fig


def create_song_patterns_plot(data):
    """Create a plot showing song selection patterns."""
    plot_data = []

    for model, temp_data in data.items():
        for temp, songs in temp_data.items():
            song_counts = Counter(
                f"{song['song']} - {song['artist']}" for song in songs
            )

            # Get top 10 songs
            for song, count in song_counts.most_common(10):
                plot_data.append(
                    {
                        "model": model,
                        "temperature": temp,
                        "song": song,
                        "count": count,
                    }
                )

    df = pd.DataFrame(plot_data)

    fig = go.Figure()

    for model in df["model"].unique():
        model_data = df[df["model"] == model]

        for temp in model_data["temperature"].unique():
            temp_data = model_data[model_data["temperature"] == temp]

            fig.add_trace(
                go.Bar(
                    name=f"{model} (T={temp})",
                    x=temp_data["song"],
                    y=temp_data["count"],
                    text=temp_data["count"],
                    textposition="auto",
                    hovertemplate="%{x}<br>" + "Count: %{y}<br>" + "<extra></extra>",
                )
            )

    fig.update_layout(
        title="Top 10 Songs by Model and Temperature",
        xaxis_title="Song",
        yaxis_title="Count",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.2)", borderwidth=1
        ),
        margin=dict(
            t=50, l=50, r=50, b=150
        ),  # Larger bottom margin for long song names
        height=600,
        width=1000,
        barmode="group",
    )

    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)

    return fig


def generate_temperature_analysis():
    """Generate all plots and statistics for temperature analysis."""
    data = load_temperature_data()

    return {
        "stats": calculate_model_stats(data),
        "plots": {
            "diversity": create_diversity_plot(data),
            "genre": create_genre_distribution_plot(data),
            "patterns": create_song_patterns_plot(data),
        },
        "models": list(data.keys()),
    }
