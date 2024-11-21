import os
import shutil
from app import create_static_site

# Build site into docs directory (GitHub Pages will use this)
DOCS_DIR = "docs"

# Clean up existing docs directory
if os.path.exists(DOCS_DIR):
    shutil.rmtree(DOCS_DIR)

# Create static site
create_static_site(DOCS_DIR)

print(f"✨ Static site built in {DOCS_DIR}/")
print("🚀 Ready for GitHub Pages!")
