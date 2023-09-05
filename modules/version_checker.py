from modules.imports import *

version = "1.0.9984"
ScriptCreator = "cyberofficial"
GitHubRepo = "https://github.com/cyberofficial/Synthalingua"
repo_owner = "cyberofficial"
repo_name = "Synthalingua"

def get_remote_version(repo_owner, repo_name, updatebranch, file_path):
    url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{updatebranch}/{file_path}"
    response = requests.get(url)

    # if the response failed then return None
    if response.status_code != 200:
        print(f"{Fore.RED}An error occurred when checking for updates. Status code: {response.status_code}{Style.RESET_ALL}")
        print(f"Could not fetch remote version from: {Fore.YELLOW}{url}{Style.RESET_ALL}")
        print(f"Please check your internet connection and try again.")
        print("\n\n")
        return None

    if response.status_code == 200:
        remote_file_content = response.text
        version_search = re.search(r'version\s*=\s*"([\d.]+)"', remote_file_content)
        if version_search:
            remote_version = version_search.group(1)
            return remote_version
        else:
            print(f"{Fore.RED}Error: Version not found in the remote file.{Style.RESET_ALL}")
            return None
    else:
        print(f"{Fore.RED}An error occurred when checking for updates. Status code: {response.status_code}{Style.RESET_ALL}")
        print(f"Could not fetch remote version from: {Fore.YELLOW}{url}{Style.RESET_ALL}")
        print(f"Please check your internet connection and try again.")
        print("\n\n")
        return None

def check_for_updates(updatebranch):
    local_version = version
    remote_version = get_remote_version(repo_owner, repo_name, updatebranch, "modules/version_checker.py")

    # if the response failed then return None
    if remote_version is None:
        return

    if remote_version is not None:
        # Split the version numbers into parts (major, minor, patch)
        local_version_parts = [int(part) for part in local_version.split(".")]
        remote_version_parts = [int(part) for part in remote_version.split(".")]

        # Compare major versions
        if remote_version_parts[0] > local_version_parts[0]:
            print(f"Major version mismatch. Local version: {Fore.YELLOW}{local_version}{Style.RESET_ALL}, remote version: {Fore.YELLOW}{remote_version}{Style.RESET_ALL}")
            print("Consider updating to the latest version.")
            print(f"Update available at: {GitHubRepo}")
            print("\n\n")
        elif remote_version_parts[0] == local_version_parts[0]:
            # Compare minor versions
            if remote_version_parts[1] > local_version_parts[1]:
                print(f"Minor version mismatch. Local version: {Fore.YELLOW}{local_version}{Style.RESET_ALL}, remote version: {Fore.YELLOW}{remote_version}{Style.RESET_ALL}")
                print("Consider updating to the latest version.")
                print(f"Update available at: {GitHubRepo}")
                print("\n\n")
            elif remote_version_parts[1] == local_version_parts[1]:
                # Compare patch versions
                if remote_version_parts[2] > local_version_parts[2]:
                    print(f"Patch version mismatch. Local version: {Fore.YELLOW}{local_version}{Style.RESET_ALL}, remote version: {Fore.YELLOW}{remote_version}{Style.RESET_ALL}")
                    print("Consider updating to the latest version.")
                    print(f"Update available at: {GitHubRepo}")
                    print("\n\n")
                else:
                    print("You are already using the latest version.")
                    print(f"Current version: {local_version}")
                    print("\n\n")
            else:
                print("You are already using a newer version.")
                print(f"Current version: {local_version}")
                print("\n\n")
        else:
            print("You are already using a newer version.")
            print(f"Current version: {local_version}")
            print("\n\n")

print("Version Checker Module Loaded")
