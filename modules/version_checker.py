"""
Version Checker Module

This module provides functionality to check and compare version numbers between
local and remote instances of the application. It supports semantic versioning
with major.minor.patch format (e.g., 1.2.3).

Features:
- Fetches the latest release version directly from a specified GitHub repository
  using the GitHub API.
- Performs semantic version comparison (major, minor, and patch levels).
- Provides colored output for better readability of update notifications and errors.
- Includes basic error handling for network issues and API response problems.
- Notifies the user if a newer version is available, if they are using the latest
  version, or if their local version is newer than the latest release.

The module uses the GitHub API's 'releases/latest' endpoint to get the most
recent tagged release and extracts the tag name as the remote version.
"""

import requests
import re
import json
from typing import Optional
from colorama import Fore, Style, init

# Initialize colorama for colored output
init()

# --- Configuration --- #
# Local version of the script
version = "1.2.3"
# Creator of the script (for display purposes)
ScriptCreator = "cyberofficial"
# URL of the GitHub repository
GitHubRepo = "https://github.com/cyberofficial/Synthalingua"
# Owner of the GitHub repository
repo_owner = "cyberofficial"
# Name of the GitHub repository
repo_name = "Synthalingua"

# --- Functions --- #

def get_remote_version() -> Optional[str]:
    """
    Fetches the latest release version tag from the configured GitHub repository
    using the GitHub API.

    This function constructs the API URL for the latest release endpoint and sends
    a GET request. It handles potential network errors, non-200 HTTP responses,
    and issues with parsing the JSON response or finding the 'tag_name'.

    Returns:
        Optional[str]: The latest version string (tag name) from the GitHub release
                      if successfully retrieved and parsed. Returns None if any error
                      occurs during the process.
    """
    # Construct the API URL for fetching the latest release
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    print(f"Attempting to fetch latest release from: {Fore.CYAN}{api_url}{Style.RESET_ALL}")
    try:
        # Send GET request to the GitHub API
        response = requests.get(api_url)
        # Raise an HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response
        release_data = response.json()
        # Extract the tag name, which represents the version
        remote_version = release_data.get("tag_name")

        if remote_version:
            # Remove 'v' prefix if it exists (e.g., v1.2.3 -> 1.2.3) to match local format
            if remote_version.startswith('v'):
                remote_version = remote_version[1:]
            print(f"Successfully fetched remote version: {Fore.YELLOW}{remote_version}{Style.RESET_ALL}")
            return remote_version
        else:
            # Handle case where 'tag_name' is not found in the response
            print(f"{Fore.RED}Error: Could not find 'tag_name' in the latest release data from {api_url}.{Style.RESET_ALL}")
            return None

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (e.g., connection refused, timeout)
        print(f"{Fore.RED}An error occurred while fetching the latest release from GitHub API ({api_url}): {e}{Style.RESET_ALL}")
        return None
    except json.JSONDecodeError:
        # Handle errors during JSON parsing
        print(f"{Fore.RED}Error: Could not decode JSON response from GitHub API. Received unexpected data.{Style.RESET_ALL}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        print(f"{Fore.RED}An unexpected error occurred during remote version check: {e}{Style.RESET_ALL}")
        return None


def check_for_updates() -> None:
    """
    Checks for updates by comparing the local script version with the latest
    release version fetched from the configured GitHub repository.

    This function calls `get_remote_version` to get the latest remote tag.
    If successful, it performs a semantic comparison (major.minor.patch).
    It prints messages indicating whether an update is available (major, minor,
    or patch mismatch), if the user is on the latest version, or if their local
    version is newer than the latest release.
    Handles potential errors during version string parsing.
    """
    local_version = version
    print(f"Local version: {Fore.YELLOW}{local_version}{Style.RESET_ALL}")
    remote_version = get_remote_version()

    # If fetching the remote version failed, exit the update check
    if remote_version is None:
        print(f"{Fore.YELLOW}Skipping update check due to error fetching remote version.{Style.RESET_ALL}")
        print("\n") # Add some spacing
        return

    # Proceed with version comparison if remote version was successfully fetched
    if remote_version is not None:
        try:
            # Split the version numbers into parts (major, minor, patch) for comparison
            local_version_parts = [int(part) for part in local_version.split(".")]
            remote_version_parts = [int(part) for part in remote_version.split(".")]
        except ValueError:
            # Handle cases where version strings are not in the expected format
            print(f"{Fore.RED}Error: Could not parse version strings for comparison.{Style.RESET_ALL}")
            print(f"Local format: {Fore.YELLOW}{local_version}{Style.RESET_ALL}, Remote format: {Fore.YELLOW}{remote_version}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Skipping version comparison.{Style.RESET_ALL}")
            print("\n") # Add some spacing
            return

        # --- Semantic Version Comparison (Major.Minor.Patch) ---

        # Compare major versions
        if remote_version_parts[0] > local_version_parts[0]:
            print(f"Major version mismatch. Local: {Fore.YELLOW}{local_version}{Style.RESET_ALL}, Remote: {Fore.YELLOW}{remote_version}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}A significant update is available!{Style.RESET_ALL}")
            print(f"Consider updating to the latest version from: {Fore.CYAN}{GitHubRepo}{Style.RESET_ALL}")
            print("\n") # Add some spacing
        elif remote_version_parts[0] == local_version_parts[0]:
            # If major versions match, compare minor versions
            if remote_version_parts[1] > local_version_parts[1]:
                print(f"Minor version mismatch. Local: {Fore.YELLOW}{local_version}{Style.RESET_ALL}, Remote: {Fore.YELLOW}{remote_version}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}A minor update is available.{Style.RESET_ALL}")
                print(f"Consider updating to the latest version from: {Fore.CYAN}{GitHubRepo}{Style.RESET_ALL}")
                print("\n") # Add some spacing
            elif remote_version_parts[1] == local_version_parts[1]:
                # If minor versions match, compare patch versions
                if remote_version_parts[2] > local_version_parts[2]:
                    print(f"Patch version mismatch. Local: {Fore.YELLOW}{local_version}{Style.RESET_ALL}, Remote: {Fore.YELLOW}{remote_version}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}A patch update is available.{Style.RESET_ALL}")
                    print(f"Consider updating to the latest version from: {Fore.CYAN}{GitHubRepo}{Style.RESET_ALL}")
                    print("\n") # Add some spacing
                else:
                    # If all parts are equal or local patch is newer, user is on latest or newer
                    print(f"{Fore.GREEN}You are already using the latest version ({Fore.YELLOW}{local_version}{Style.RESET_ALL}).{Style.RESET_ALL}")
                    print("\n") # Add some spacing
            else:
                # Local minor version is newer than remote minor version
                print(f"{Fore.YELLOW}You are using a newer version ({Fore.YELLOW}{local_version}{Style.RESET_ALL}) than the latest release ({Fore.YELLOW}{remote_version}{Style.RESET_ALL}).{Style.RESET_ALL}")
                print("\n") # Add some spacing
        else:
            # Local major version is newer than remote major version
            print(f"{Fore.YELLOW}You are using a newer version ({Fore.YELLOW}{local_version}{Style.RESET_ALL}) than the latest release ({Fore.YELLOW}{remote_version}{Style.RESET_ALL}).{Style.RESET_ALL}")
            print("\n") # Add some spacing