# LLM Jukebox

A Python project that generates music playlists using various Large Language Models through OpenRouter API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
- Copy `.env.example` to `.env`
- Add your OpenRouter API key to `.env`

## Usage

Run the playlist generator:
```bash
python playlist_generator.py
```

The script will generate a playlist in JSON format with 10 songs based on the LLM's response.

## Response Format

The playlist is returned in the following JSON format:
```json
{
    "playlist": [
        {
            "artist": "Artist Name",
            "song": "Song Title"
        }
    ]
}
```
