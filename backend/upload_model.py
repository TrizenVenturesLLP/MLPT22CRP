import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, create_repo, upload_file

# Load environment variables
load_dotenv()

def upload_to_hf():
    # 1. Configuration
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Error: HF_TOKEN not found in .env file.")
        return

    # User can change these
    repo_name = "trend-classifier" # Change if you want a different repo name
    local_model_path = Path("models/trend_classifier.pkl")
    
    if not local_model_path.exists():
        print(f"Error: Local model file not found at {local_model_path}")
        return

    api = HfApi(token=token)
    user = api.whoami()
    username = user['name']
    repo_id = f"{username}/{repo_name}"

    print(f"Target Repository: {repo_id}")

    # 2. Create repo if it doesn't exist
    try:
        create_repo(repo_id=repo_id, token=token, repo_type="model", exist_ok=True)
        print(f"Repository {repo_id} is ready.")
    except Exception as e:
        print(f"Error creating/accessing repository: {e}")
        return

    # 3. Upload the file
    print(f"Uploading {local_model_path} to {repo_id}...")
    try:
        api.upload_file(
            path_or_fileobj=str(local_model_path),
            path_in_repo="trend_classifier.pkl",
            repo_id=repo_id,
            repo_type="model",
        )
        print("\n" + "="*50)
        print("SUCCESS! Model uploaded successfully.")
        print(f"New Repo ID: {repo_id}")
        print("Update your HF_TREND_REPO_ID environment variable on Render to this value.")
        print("="*50)
    except Exception as e:
        print(f"Error uploading file: {e}")

if __name__ == "__main__":
    upload_to_hf()
