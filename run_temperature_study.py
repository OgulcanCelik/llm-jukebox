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

# Define models to test
MODELS = ["anthropic/claude-3-5-haiku", "meta-llama/llama-3.3-70b-instruct"]

# Temperature settings to test
TEMPERATURES = [0.1, 0.8]

# Number of runs per model/temperature combination
RUNS_PER_CONFIG = 40

# Whether to pause on error
PAUSE_ON_ERROR = True


def ensure_output_directory(experiment_type, count, temp):
    """Create and return the output directory for a specific experiment configuration."""
    base_dir = Path("outputs")
    experiment_dir = base_dir / f"{experiment_type}_{count}_temp_{temp:.1f}"
    experiment_dir.mkdir(exist_ok=True, parents=True)
    return experiment_dir


def get_output_filepath(experiment_dir, model_name, run_number):
    """Generate output filepath for a specific run."""
    clean_model_name = model_name.replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (
        experiment_dir / f"playlist_{clean_model_name}_run{run_number}_{timestamp}.json"
    )


def create_playlist(model, temperature=0.7):
    """Generate a playlist using the specified model and temperature."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
    )

    try:
        completion = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": 'Give me a playlist in song - artist format for 10 songs based on how you feel. Nothing else, just songs in json I mentioned. nothing else. For example, the following is a valid response: {"songs": [{ "song": "", "artist": "" }]} .',
                }
            ],
            temperature=temperature,
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
    """Save the playlist to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(playlist, f, indent=2)


def save_error_log(model, experiment_type, count, temp, run_number, raw_response):
    """Save error information to a log file."""
    error_dir = Path("outputs") / "error_logs"
    error_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = (
        error_dir
        / f"error_{model.replace('/', '_')}_{experiment_type}_{count}_temp_{temp:.1f}_run_{run_number}_{timestamp}.txt"
    )

    with open(error_file, "w") as f:
        f.write(f"Model: {model}\n")
        f.write(f"Experiment: {experiment_type}_{count}\n")
        f.write(f"Temperature: {temp}\n")
        f.write(f"Run: {run_number}\n")
        f.write(f"Raw Response:\n{raw_response}\n")


def count_existing_runs(experiment_dir, model):
    """Count how many successful runs already exist for a model."""
    clean_model_name = model.replace("/", "_")
    existing_files = list(experiment_dir.glob(f"playlist_{clean_model_name}_*.json"))
    return len(existing_files)


def run_temperature_experiments(continue_from_last=True):
    """Run the temperature study experiments."""
    print("\nRunning temperature experiments...")

    for temp in TEMPERATURES:
        print(f"\nTemperature: {temp}")
        experiment_dir = ensure_output_directory(
            "temperature_study", RUNS_PER_CONFIG, temp
        )

        for model in MODELS:
            existing_runs = (
                count_existing_runs(experiment_dir, model) if continue_from_last else 0
            )
            if existing_runs >= RUNS_PER_CONFIG:
                print(
                    f"\nModel: {model} - Already completed {existing_runs} runs, skipping..."
                )
                continue

            print(f"\nModel: {model} - Continuing from run {existing_runs + 1}")

            for run in range(existing_runs, RUNS_PER_CONFIG):
                print(f"Run {run + 1}/{RUNS_PER_CONFIG}...", end=" ")
                sys.stdout.flush()

                result = create_playlist(model, temperature=temp)
                if result is not None:
                    playlist, raw_response = result
                    if playlist:
                        filepath = get_output_filepath(experiment_dir, model, run + 1)
                        save_playlist(playlist, filepath)
                        print("✓")
                    else:
                        print("✗")
                        save_error_log(
                            model,
                            "temperature_study",
                            RUNS_PER_CONFIG,
                            temp,
                            run + 1,
                            raw_response,
                        )
                else:
                    print("✗")
                    save_error_log(
                        model,
                        "temperature_study",
                        RUNS_PER_CONFIG,
                        temp,
                        run + 1,
                        "Failed to generate playlist",
                    )


if __name__ == "__main__":
    run_temperature_experiments(continue_from_last=True)
