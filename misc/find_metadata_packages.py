import os
import sys
from pathlib import Path

def find_metadata_users():
    """
    Scans the site-packages of the current environment to find packages
    that use importlib.metadata and prints them as Nuitka flags.
    """
    print("Scanning for packages that use 'importlib.metadata'...")

    # Find the site-packages directory
    try:
        # Get the path of the current python executable
        # sys.executable gives you the path to the python.exe running the script
        # e.g., E:\Synthalingua\Synthalingua_Main\data_whisper\Scripts\python.exe
        # We need to go up two directories and then into Lib/site-packages
        env_path = Path(sys.executable).parent.parent
        site_packages = env_path / "Lib" / "site-packages"

        if not site_packages.is_dir():
            print(f"Error: Could not find site-packages at {site_packages}")
            return
    except Exception as e:
        print(f"Error finding environment path: {e}")
        return

    found_distributions = set()

    for root, _, files in os.walk(site_packages):
        # We want to ignore the dist-info directories themselves
        if ".dist-info" in root:
            continue

        for filename in files:
            if filename.endswith(".py"):
                file_path = Path(root) / filename
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # Check if the file imports or uses importlib.metadata
                        if "importlib.metadata" in content:
                            # Find the corresponding .dist-info directory to get the official name
                            relative_path = file_path.relative_to(site_packages)
                            # The first part of the relative path is the package name
                            package_name = relative_path.parts[0]
                            
                            # Now find the matching dist-info directory
                            for item in site_packages.iterdir():
                                if item.is_dir() and item.name.endswith(".dist-info"):
                                    # e.g., coloredlogs-15.0.1.dist-info
                                    dist_name = item.name.split("-")[0]
                                    if dist_name.lower() == package_name.lower().replace("_", "-"):
                                        found_distributions.add(dist_name)
                                        break
                except Exception:
                    # Ignore files that can't be read
                    continue

    if not found_distributions:
        print("No packages using importlib.metadata were found.")
        return

    print("\n--- Nuitka Flags Found ---")
    print("Copy the flags below and add them to your build command:\n")
    for dist in sorted(list(found_distributions)):
        print(f"--include-distribution-metadata={dist}")

if __name__ == "__main__":
    find_metadata_users()