"""
Fetch the bundled FFmpeg and yt-dlp tools used by packaged builds.

build.bat runs this before building. The tools land in downloaded_assets next
to this script in the exact layout set_up_env expects, so the packaged
set_up_env.exe only has to configure paths and the build only has to copy
them into the patch folder.

Each run contacts upstream and downloads fresh unless the staged copy is
already the same:

- FFmpeg: a HEAD request on the rolling gyan.dev build identifies the exact
  artifact (ETag, Last-Modified, Content-Length). A staged copy matching any
  of those is current and the download is skipped.
- yt-dlp: the GitHub release feed gives the latest tag. A staged executable
  reporting that exact version is current and the download is skipped. The
  archive is saved named after its tag.

Both tools are verified after extraction: the executable must exist and run,
and yt-dlp must report the tag it came from. A failed or corrupt download
never replaces a working staged copy, because the swap happens only after
verification passes.

Usage (normally invoked by build.bat with the venv active):
    python fetch_bundled_tools.py [--staging <dir>] [--force]

    --force    Download fresh even when the staged copies look current.
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
import zipfile
from hashlib import sha256
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_STAGING = SCRIPT_DIR / 'downloaded_assets'
MANIFEST_NAME = 'bundled_tools_manifest.json'

FFMPEG_URL = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z'
YTDLP_LATEST_API = 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'
YTDLP_ASSET_NAME = 'yt-dlp_win.zip'
SEVEN_ZIP_URL = 'https://www.7-zip.org/a/7zr.exe'


def sha256_of(path: Path) -> str:
    """Hash a file in chunks."""
    digest = sha256()
    with open(path, 'rb') as handle:
        while True:
            buffer = handle.read(2 ** 20)
            if not buffer:
                break
            digest.update(buffer)
    return digest.hexdigest()


def download_to(url: str, dest: Path, expected_size: int = None) -> None:
    """
    Stream a download to dest through a .part file.

    The partial file is renamed into place only after the transfer completes,
    and the size is checked against the server's Content-Length when both are
    known, so an interrupted download never leaves a broken archive behind.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part_path = Path(str(dest) + '.part')
    print(f"Downloading {url}")
    try:
        with requests.get(url, stream=True, timeout=(15, 120)) as response:
            response.raise_for_status()
            total = int(response.headers.get('Content-Length') or 0)
            if expected_size and total and total != expected_size:
                raise RuntimeError(
                    f"size mismatch for {dest.name}: server reports {total} bytes, "
                    f"expected {expected_size}")
            done = 0
            shown = -1
            with open(part_path, 'wb') as output:
                for chunk in response.iter_content(chunk_size=1024 * 512):
                    output.write(chunk)
                    done += len(chunk)
                    if total:
                        percent = min(100, done * 100 // total)
                        if percent >= shown + 10 or percent == 100:
                            print(f"\r  {dest.name}: {percent}%", end='', flush=True)
                            shown = percent
        print()
        if expected_size and done != expected_size:
            raise RuntimeError(
                f"incomplete download for {dest.name}: got {done} of {expected_size} bytes")
    except Exception:
        if part_path.exists():
            part_path.unlink()
        raise
    part_path.replace(dest)


def head_info(url: str):
    """Return {'etag', 'last_modified', 'size'} for a URL, or None on failure."""
    try:
        response = requests.head(url, timeout=30, allow_redirects=True)
        if response.status_code == 200:
            size = int(response.headers.get('Content-Length') or 0) or None
            return {
                'etag': response.headers.get('ETag'),
                'last_modified': response.headers.get('Last-Modified'),
                'size': size,
            }
        print(f"  HEAD request for {url} returned status {response.status_code}")
    except Exception as error:
        print(f"  HEAD request for {url} failed: {error}")
    return None


def get_ytdlp_latest():
    """Return (tag, zip download url) for the newest yt-dlp release, or (None, None)."""
    try:
        response = requests.get(
            YTDLP_LATEST_API,
            timeout=30,
            headers={'User-Agent': 'Synthalingua-build'},
        )
        response.raise_for_status()
        data = response.json()
        tag = data.get('tag_name')
        asset = next(
            (item for item in data.get('assets', []) if item.get('name') == YTDLP_ASSET_NAME),
            None,
        )
        if tag and asset:
            return tag, asset['browser_download_url']
        print(f"  Release feed did not list {YTDLP_ASSET_NAME} for tag {tag}")
    except Exception as error:
        print(f"  Could not query the yt-dlp release feed: {error}")
    return None, None


def run_tool_version(executable: Path, argument: str = '--version'):
    """Run an executable and return its first output line, or None on failure."""
    try:
        result = subprocess.run(
            [str(executable), argument],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def find_single_file(root: Path, name: str):
    """Locate a file by name anywhere under root."""
    try:
        return next(root.rglob(name))
    except StopIteration:
        return None


def ensure_7zr(staging: Path) -> str:
    """Return a 7z extractor command, downloading 7zr.exe on Windows if needed."""
    if platform.system().lower() == 'windows':
        seven_zip = staging / '7zr.exe'
        if not seven_zip.exists():
            print("7zr.exe not staged, downloading it for extraction...")
            download_to(SEVEN_ZIP_URL, seven_zip)
        return str(seven_zip)
    for candidate in ('7z', 'p7zip'):
        found = shutil.which(candidate)
        if found:
            return found
    raise RuntimeError("no 7-zip extractor available on this system")


def update_ffmpeg(staging: Path, manifest: dict, force: bool) -> bool:
    """Make the staged FFmpeg current. Returns True when the staging is usable."""
    ffmpeg_dir = staging / 'ffmpeg'
    ffmpeg_exe = find_single_file(ffmpeg_dir, 'ffmpeg.exe') if ffmpeg_dir.is_dir() else None
    entry = manifest.get('ffmpeg')
    info = head_info(FFMPEG_URL)

    if not force and ffmpeg_exe and entry and info:
        matched = None
        if info.get('etag') and info.get('etag') == entry.get('etag'):
            matched = 'ETag'
        elif info.get('last_modified') and info.get('last_modified') == entry.get('last_modified'):
            matched = 'Last-Modified'
        elif info.get('size') and info.get('size') == entry.get('size'):
            matched = 'archive size'
        if matched:
            print(f"Bundled FFmpeg is current ({entry.get('version', 'unknown version')}), "
                  f"skipping download ({matched} matches upstream).")
            return True

    # No manifest yet, but the staged archive may already be the current build.
    if not force and not entry and ffmpeg_exe and info and info.get('size'):
        archive = staging / 'ffmpeg.7z'
        if archive.exists() and archive.stat().st_size == info['size']:
            version_line = run_tool_version(ffmpeg_exe, '-version')
            if version_line:
                version = version_line.split()[2] if len(version_line.split()) > 2 else version_line
                manifest['ffmpeg'] = {
                    'url': FFMPEG_URL,
                    'etag': info.get('etag'),
                    'last_modified': info.get('last_modified'),
                    'size': info['size'],
                    'archive_sha256': sha256_of(archive),
                    'version': version,
                }
                print(f"Bundled FFmpeg is current ({version}), adopting it into the manifest.")
                return True

    if not info:
        print("Could not identify the upstream FFmpeg build; downloading fresh.")

    archive = staging / 'ffmpeg.7z'
    download_to(FFMPEG_URL, archive, expected_size=info.get('size') if info else None)

    seven_zip = ensure_7zr(staging)
    temp_dir = staging / '_temp_fetch_ffmpeg'
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    try:
        print(f"Extracting {archive.name}...")
        result = subprocess.run(
            [seven_zip, 'x', str(archive), f'-o{temp_dir}'],
            check=True,
            capture_output=True,
            text=True,
        )

        extracted = [item for item in temp_dir.iterdir()
                     if item.is_dir() and 'ffmpeg' in item.name.lower()]
        if not extracted:
            raise RuntimeError("the archive did not contain an ffmpeg folder")
        new_dir = extracted[0]

        new_exe = find_single_file(new_dir, 'ffmpeg.exe')
        if not new_exe:
            raise RuntimeError("ffmpeg.exe was not found in the extracted archive")
        version_line = run_tool_version(new_exe, '-version')
        if not version_line:
            raise RuntimeError(f"extracted ffmpeg.exe at {new_exe} did not run")
        version = version_line.split()[2] if len(version_line.split()) > 2 else version_line

        # Swap only after the extraction verified, so a bad download never
        # destroys a working staged copy.
        if ffmpeg_dir.exists():
            shutil.rmtree(ffmpeg_dir)
        new_dir.rename(ffmpeg_dir)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    manifest['ffmpeg'] = {
        'url': FFMPEG_URL,
        'etag': info.get('etag') if info else None,
        'last_modified': info.get('last_modified') if info else None,
        'size': archive.stat().st_size,
        'archive_sha256': sha256_of(archive),
        'version': version,
    }
    print(f"Bundled FFmpeg updated to {version}.")
    return True


def update_ytdlp(staging: Path, manifest: dict, force: bool) -> bool:
    """Make the staged yt-dlp current. Returns True when the staging is usable."""
    ytdlp_dir = staging / 'yt-dlp_win'
    exe = ytdlp_dir / 'yt-dlp.exe'
    tag, zip_url = get_ytdlp_latest()
    entry = manifest.get('ytdlp')

    if tag is None:
        if exe.exists():
            print("WARNING: could not determine the latest yt-dlp release; "
                  "keeping the staged copy without a freshness check.")
            return True
        print("No staged yt-dlp and no release information available.")
        return False

    staged_version = run_tool_version(exe) if exe.exists() else None

    if not force and staged_version == tag:
        if entry and entry.get('tag') == tag:
            print(f"Bundled yt-dlp is current ({tag}), skipping download.")
        else:
            manifest['ytdlp'] = {
                'tag': tag,
                'url': zip_url,
                'archive_sha256': None,
                'version': staged_version,
            }
            print(f"Bundled yt-dlp is current ({tag}), adopting it into the manifest.")
        return True

    archive = staging / f'yt-dlp_win_{tag}.zip'
    download_to(zip_url, archive)

    temp_dir = staging / '_temp_fetch_ytdlp'
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    try:
        print(f"Extracting {archive.name}...")
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(temp_dir)

        new_exe = temp_dir / 'yt-dlp.exe'
        if not new_exe.exists():
            new_exe = find_single_file(temp_dir, 'yt-dlp.exe')
        if not new_exe:
            raise RuntimeError("yt-dlp.exe was not found in the extracted archive")
        extracted_version = run_tool_version(new_exe)
        if extracted_version != tag:
            raise RuntimeError(
                f"extracted yt-dlp reports {extracted_version!r}, expected {tag!r}")

        if ytdlp_dir.exists():
            shutil.rmtree(ytdlp_dir)
        temp_dir.rename(ytdlp_dir)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    manifest['ytdlp'] = {
        'tag': tag,
        'url': zip_url,
        'archive_sha256': sha256_of(archive),
        'version': extracted_version,
    }
    print(f"Bundled yt-dlp updated to {tag}.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch the bundled FFmpeg and yt-dlp for packaged builds.")
    parser.add_argument('--staging', type=Path, default=DEFAULT_STAGING,
                        help="Folder to stage the tools in (default: downloaded_assets next to this script).")
    parser.add_argument('--force', action='store_true',
                        help="Download fresh even when the staged copies look current.")
    args = parser.parse_args()

    staging: Path = args.staging
    staging.mkdir(parents=True, exist_ok=True)
    manifest_path = staging / MANIFEST_NAME

    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except Exception as error:
            print(f"WARNING: could not read {manifest_path} ({error}); refetching.")
            manifest = {}

    print(f"Staging folder: {staging}")
    ok = True
    try:
        if not update_ffmpeg(staging, manifest, args.force):
            ok = False
    except Exception as error:
        print(f"ERROR fetching FFmpeg: {error}")
        ok = False
    try:
        if not update_ytdlp(staging, manifest, args.force):
            ok = False
    except Exception as error:
        print(f"ERROR fetching yt-dlp: {error}")
        ok = False

    try:
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    except Exception as error:
        print(f"WARNING: could not write {manifest_path}: {error}")

    if ok:
        ffmpeg_version = (manifest.get('ffmpeg') or {}).get('version', 'unknown')
        ytdlp_version = (manifest.get('ytdlp') or {}).get('tag', 'unknown')
        print(f"Bundled tools ready: FFmpeg {ffmpeg_version}, yt-dlp {ytdlp_version}")
        return 0
    print("Fetching bundled tools did not complete.")
    return 1


if __name__ == '__main__':
    sys.exit(main())
