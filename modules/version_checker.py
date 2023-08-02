import requests
import re

version = "1.0.9971"
ScriptCreator = "cyberofficial"
GitHubRepo = "https://github.com/cyberofficial/Synthalingua"
repo_owner = "cyberofficial"
repo_name = "Synthalingua"

def get_remote_version(repo_owner, repo_name, file_path):
    url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/master/{file_path}"
    response = requests.get(url)

    if response.status_code == 200:
        remote_file_content = response.text
        version_search = re.search(r'version\s*=\s*"([\d.]+)"', remote_file_content)
        if version_search:
            remote_version = version_search.group(1)
            return remote_version
        else:
            print("Error: Version not found in the remote file.")
            return None
    else:
        print(f"An error occurred. Status code: {response.status_code}")
        return None

def check_for_updates():
    local_version = version
    remote_version = get_remote_version(repo_owner, repo_name, "transcribe_audio.py")

    if remote_version is not None:
        if remote_version != local_version:
            print(f"Version mismatch. Local version: {local_version}, remote version: {remote_version}")
            print("Consider updating to the latest version.")
            print(f"Update available at: " + GitHubRepo)
            print("\n\n\n\n\n\n")
        else:
            print("You are already using the latest version.")
            print(f"Current version: {local_version}")
            print("\n\n\n\n\n\n")

print("Version Checker Module Loaded")