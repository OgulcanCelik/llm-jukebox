# LLM Jukebox 🎵

An experimental project to analyze music preferences across different Large Language Models.

## Features

- Multi-model music playlist analysis
- Genre visualization and analysis
- Model comparison and diversity metrics
- Interactive visualizations using Plotly

## Deployment

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the Flask server:
```bash
python app.py
```

### GitHub Pages Deployment

1. Build the static site:
```bash
python build_site.py
```

2. Push to GitHub:
```bash
git add docs/
git commit -m "Update GitHub Pages site"
git push
```

3. Enable GitHub Pages:
- Go to your repository settings
- Under "GitHub Pages", select "main" branch and "/docs" folder
- Save the changes

The site will be available at: `https://[your-username].github.io/llm-jukebox/`

## License

MIT License
