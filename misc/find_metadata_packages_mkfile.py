import os
import sys
from pathlib import Path

# The name of the file where the Nuitka flags will be saved.
OUTPUT_FILENAME = "nuitka_metadata_args.txt"

def find_metadata_users():
    """
    Scans the site-packages of the current environment to find packages
    that use importlib.metadata and saves them as Nuitka flags to a file.
    """
    print("Scanning for packages that use 'importlib.metadata'...")

    try:
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
        if ".dist-info" in root:
            continue

        for filename in files:
            if filename.endswith(".py"):
                file_path = Path(root) / filename
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if "importlib.metadata" in content:
                            relative_path = file_path.relative_to(site_packages)
                            package_name = relative_path.parts[0]
                            
                            for item in site_packages.iterdir():
                                if item.is_dir() and item.name.endswith(".dist-info"):
                                    dist_name = item.name.split("-")[0]
                                    if dist_name.lower() == package_name.lower().replace("_", "-"):
                                        found_distributions.add(dist_name)
                                        break
                except Exception:
                    continue

    if not found_distributions:
        print("No packages using importlib.metadata were found.")
        return

    # --- Save the flags to the output file ---
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            for dist in sorted(list(found_distributions)):
                # Write each flag on a new line for clarity
                f.write(f"--include-distribution-metadata={dist}\n")
        
        print("\n--- Nuitka Flags Generated ---")
        print(f"Successfully saved {len(found_distributions)} metadata flags to '{OUTPUT_FILENAME}'")
    except Exception as e:
        print(f"\nError writing to {OUTPUT_FILENAME}: {e}")


if __name__ == "__main__":
    find_metadata_users()