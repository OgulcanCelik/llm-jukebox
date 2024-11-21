import os
import shutil
from app import create_static_site

def main():
    # Create dist directory if it doesn't exist
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Generate static site
    create_static_site(dist_dir)
    
    print(f"Static site generated in {dist_dir}/")
    print("You can now deploy this directory to Netlify or any static hosting service!")

if __name__ == "__main__":
    main()
