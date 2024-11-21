import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from pathlib import Path
from datetime import datetime
import sys
from json_repair import repair_json

# Load environment variables
load_dotenv()

# Define models
MODELS = [
    # "anthropic/claude-3-haiku",
    # "anthropic/claude-3.5-sonnet",
    # "anthropic/claude-3-opus",
    # "openai/chatgpt-4o-latest",
    "openai/gpt-4o-mini",
    # "openai/o1-mini",
    # "google/gemini-flash-1.5",
    # "google/gemini-exp-1114"
]

# Number of runs per model
RUNS_PER_MODEL = 10

# Whether to pause on error
PAUSE_ON_ERROR = True

def ensure_output_directory():
    base_dir = Path("outputs")
    base_dir.mkdir(exist_ok=True)
    return base_dir

def get_output_filepath(model_name, run_number):
    # Create a clean model name for filesystem
    clean_model_name = model_name.replace('/', '_')
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create model-specific directory
    base_dir = ensure_output_directory()
    model_dir = base_dir / clean_model_name
    model_dir.mkdir(exist_ok=True)
    
    # Create filename with timestamp and run number
    filename = f"playlist_run{run_number}_{timestamp}.json"
    return model_dir / filename

def create_playlist(model):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    try:
        completion = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": "Give me a playlist in song - artist format for 10 songs based on how you feel. Nothing else, just songs in json I mentioned. nothing else. For example, the following is a valid response: {\"songs\": [{ \"song\": \"\", \"artist\": \"\" }]} ."
                }
            ]
        )
        
        response = completion.choices[0].message.content
        try:
            # First try regular json parsing
            return json.loads(response), response
        except json.JSONDecodeError:
            try:
                # If regular parsing fails, try to repair the JSON
                repaired_json = repair_json(response)
                print(f"\n{'!'*50}")
                print("Original JSON was malformed, but repaired successfully.")
                print(f"Original response:\n{response}")
                print(f"Repaired JSON:\n{repaired_json}")
                print(f"{'!'*50}\n")
                
                parsed_json = json.loads(repaired_json)
                return parsed_json, response
            except Exception as e:
                print(f"\n{'!'*50}")
                print(f"JSON Repair Error: {str(e)}")
                print("Raw response:")
                print(f"{response}")
                print(f"{'!'*50}\n")
                if PAUSE_ON_ERROR:
                    input("Press Enter to continue or Ctrl+C to abort...")
                return None, response
            
    except Exception as e:
        print(f"\n{'!'*50}")
        print(f"API Error: {str(e)}")
        print(f"{'!'*50}\n")
        if PAUSE_ON_ERROR:
            input("Press Enter to continue or Ctrl+C to abort...")
        return None, str(e)

def save_playlist(playlist, filepath):
    with open(filepath, 'w') as f:
        json.dump(playlist, f, indent=2)

def save_error_log(model, run_number, raw_response):
    # Create error logs directory
    base_dir = ensure_output_directory()
    error_dir = base_dir / "error_logs"
    error_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = error_dir / f"error_{model.replace('/', '_')}_run{run_number}_{timestamp}.txt"
    
    with open(error_file, 'w') as f:
        f.write(f"Model: {model}\n")
        f.write(f"Run: {run_number}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("\nRaw Response:\n")
        f.write(str(raw_response))
    
    print(f"Error log saved to: {error_file}")

def generate_playlists(num_runs=10):
    total_models = len(MODELS)
    
    for model_idx, model in enumerate(MODELS, 1):
        print(f"\n{'='*50}")
        print(f"Processing model {model_idx}/{total_models}: {model}")
        print(f"{'='*50}")
        
        for run in range(1, num_runs + 1):
            try:
                print(f"\nStarting run {run}/{num_runs}...")
                result = create_playlist(model)
                playlist, raw_response = result if result else (None, None)
                
                if playlist:
                    output_path = get_output_filepath(model, run)
                    save_playlist(playlist, output_path)
                    print(f"✓ Run {run}/{num_runs} completed for {model}")
                else:
                    print(f"✗ Run {run}/{num_runs} failed for {model}")
                    if raw_response:
                        save_error_log(model, run, raw_response)
            except Exception as e:
                print(f"✗ Error in run {run}/{num_runs} for {model}: {str(e)}")
        
        print(f"\nCompleted all runs for {model}")

if __name__ == "__main__":
    generate_playlists()
