"""
Model Preloader Module

This module handles preloading and caching of models for Synthalingua.
Supports multiple model sources (Whisper, FasterWhisper, OpenVINO, Demucs) with
various configurations including English-only variants and quantization
options.

Features:
- Parse complex preload specifications (e.g., "whisper:1gb+2gb.en,faster:3gb")
- Download and cache models before main application runs
- Support for multiple model sources and variants
- Batch preloading with progress tracking
- Validation of model specifications
- Demucs models download into the local repo layout (<model_dir>/demucs) that
  `demucs --repo` consumes, with checksum verification of every file

Usage:
    from modules.model_preloader import preload_models
    
    preload_models("whisper:1gb+2gb,faster:1gb.en", model_dir="models", device="cuda")
    preload_models("demucs:all", model_dir="models")
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from colorama import Fore, Style, init

# Initialize colorama
init()


class ModelSpec:
    """Represents a single model specification with source, size, and variants."""
    
    def __init__(self, source: str, size: str, english_only: bool = False, quantization: Optional[str] = None):
        """
        Initialize model specification.
        
        Args:
            source: Model source ('whisper', 'faster', 'openvino')
            size: Model size (1gb, 2gb, 3gb, 6gb, 7gb, 11gb-v2, 11gb-v3)
            english_only: Whether to use English-only variant
            quantization: Quantization type for OpenVINO (e.g., 'int8', 'int4')
        """
        self.source = source
        self.size = size
        self.english_only = english_only
        self.quantization = quantization
    
    def to_model_name(self) -> str:
        """
        Convert specification to model name used by Whisper.
        
        Returns:
            str: Model name (e.g., 'tiny', 'base.en', 'large-v3', 'htdemucs_ft')
        """
        # Demucs uses bag names directly ('htdemucs', 'mdx_extra_q', 'all', ...)
        if self.source == 'demucs':
            return self.size
        
        # Map RAM size to model name
        size_map = {
            "1gb": "tiny",
            "2gb": "base",
            "3gb": "small",
            "6gb": "medium",
            "7gb": "turbo",
            "11gb-v2": "large-v2",
            "11gb-v3": "large-v3"
        }
        
        model_name = size_map.get(self.size.lower())
        if not model_name:
            raise ValueError(f"Invalid model size: {self.size}")
        
        # Add .en suffix for English-only models
        if self.english_only:
            model_name += ".en"
        
        return model_name
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        parts = [self.source, self.size]
        if self.english_only:
            parts.append("en")
        if self.quantization:
            parts.append(self.quantization)
        return f"ModelSpec({':'.join(parts)})"


def parse_preload_spec(spec: str) -> List[ModelSpec]:
    """
    Parse preload specification string into list of ModelSpec objects.
    
    Format: 'source:size[.variant][+size.variant,...][,source:size...]'
    
    Examples:
        "whisper:1gb" -> [ModelSpec(whisper, 1gb)]
        "faster:1gb.en" -> [ModelSpec(faster, 1gb, en=True)]
        "whisper:1gb+2gb.en" -> [ModelSpec(whisper, 1gb), ModelSpec(whisper, 2gb, en=True)]
        "whisper:1gb,faster:2gb" -> [ModelSpec(whisper, 1gb), ModelSpec(faster, 2gb)]
        "openvino:1gb.int8" -> [ModelSpec(openvino, 1gb, quant=int8)]
    
    Args:
        spec: Preload specification string
    
    Returns:
        List[ModelSpec]: List of parsed model specifications
    
    Raises:
        ValueError: If specification format is invalid
    """
    if not spec or not spec.strip():
        return []
    
    models = []
    
    # Split by comma to separate different sources
    source_specs = [s.strip() for s in spec.split(',')]
    
    for source_spec in source_specs:
        if ':' not in source_spec:
            raise ValueError(f"Invalid format '{source_spec}': expected 'source:size' (e.g., 'whisper:1gb')")
        
        # Split source and size specs
        source, sizes_spec = source_spec.split(':', 1)
        source = source.strip().lower()
        
        # Validate source
        valid_sources = ['whisper', 'faster', 'openvino', 'demucs']
        if source not in valid_sources:
            raise ValueError(f"Invalid source '{source}': must be one of {valid_sources}")
        
        # Split by + to get multiple sizes for same source
        size_specs = [s.strip() for s in sizes_spec.split('+')]
        
        for size_spec in size_specs:
            # Demucs uses model (bag) names directly instead of RAM sizes
            if source == 'demucs':
                bag_name = size_spec.strip().lower()
                if bag_name != 'all' and bag_name not in DEMUCS_BAG_NAMES:
                    raise ValueError(
                        f"Unknown demucs model '{bag_name}': must be 'all' or one of {list(DEMUCS_BAG_NAMES)}"
                    )
                models.append(ModelSpec(source='demucs', size=bag_name))
                continue
            
            # Parse size and variants (e.g., "1gb.en.int8")
            parts = size_spec.split('.')
            size = parts[0].strip().lower()
            
            # Validate size
            valid_sizes = ['1gb', '2gb', '3gb', '6gb', '7gb', '11gb-v2', '11gb-v3']
            if size not in valid_sizes:
                raise ValueError(f"Invalid size '{size}': must be one of {valid_sizes}")
            
            # Parse variants
            english_only = False
            quantization = None
            
            for variant in parts[1:]:
                variant = variant.strip().lower()
                
                if variant == 'en':
                    english_only = True
                elif variant in ['int4', 'int8', 'int16', 'float16', 'float32']:
                    if source != 'openvino':
                        print(f"{Fore.YELLOW}Warning:{Style.RESET_ALL} Quantization '{variant}' is only supported for OpenVINO. Ignoring for {source}.")
                    else:
                        quantization = variant
                else:
                    raise ValueError(f"Invalid variant '{variant}': must be 'en' or quantization type (int4/int8/int16/float16/float32)")
            
            # Validate English-only variants
            if english_only:
                # Only certain models have .en variants
                if size in ['7gb', '11gb-v2', '11gb-v3']:
                    print(f"{Fore.YELLOW}Warning:{Style.RESET_ALL} Model size '{size}' does not have an English-only variant. Loading multilingual instead.")
                    english_only = False
            
            models.append(ModelSpec(source, size, english_only, quantization))
    
    return models


def preload_model(spec: ModelSpec, model_dir: str = "models", device: str = "cuda", compute_type: str = "default") -> bool:
    """
    Preload a single model by instantiating it (which triggers download/cache).
    
    Args:
        spec: Model specification to preload
        model_dir: Root directory for model storage
        device: Device to use for loading (cuda/cpu/etc)
        compute_type: Compute type for FasterWhisper/OpenVINO
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Demucs models are downloaded into the local repo layout under
        # <model_dir>/demucs and verified by checksum, no model load needed.
        if spec.source == "demucs":
            return preload_demucs(spec.size, model_dir)
        
        model_name = spec.to_model_name()
        
        # Check if model already exists
        # Note: "turbo" resolves to the large-v3-turbo artifacts in every
        # backend (whisper's URL, faster-whisper's repo, OpenVINO's folder),
        # so the cache check must look for those names instead.
        artifact_name = "large-v3-turbo" if model_name == "turbo" else model_name
        model_exists = False
        if spec.source == "whisper":
            model_path = os.path.join(model_dir, "Whisper", f"{artifact_name}.pt")
            model_exists = os.path.exists(model_path)
        elif spec.source == "faster":
            if artifact_name == "large-v3-turbo":
                repo_dir = "models--mobiuslabsgmbh--faster-whisper-large-v3-turbo"
            else:
                repo_dir = f"models--Systran--faster-whisper-{artifact_name}"
            model_path = os.path.join(model_dir, "FasterWhisper", repo_dir)
            model_exists = os.path.exists(model_path)
        elif spec.source == "openvino":
            model_path = os.path.join(model_dir, "OpenVINO", "openai", f"whisper-{artifact_name}")
            model_exists = os.path.exists(model_path)
        
        if model_exists:
            print(f"{Fore.CYAN}[Preload]{Style.RESET_ALL} Loading {spec.source}:{spec.size} ({model_name}) - {Fore.YELLOW}[Cached]{Style.RESET_ALL}", end='', flush=True)
        else:
            print(f"{Fore.CYAN}[Preload]{Style.RESET_ALL} Downloading {spec.source}:{spec.size} ({model_name})...")
            print(f"{Fore.YELLOW}  → Download progress will be shown below...{Style.RESET_ALL}")
        
        if spec.source == "whisper":
            from modules.BaseWhisper import BaseWhisperModel
            
            # BaseWhisper doesn't use compute_type
            model = BaseWhisperModel(model_name, device=device, download_root=model_dir)
            del model  # Free memory immediately
            
        elif spec.source == "faster":
            from modules.FasterWhisper import FasterWhisperModel
            
            # Use provided compute_type or default
            model = FasterWhisperModel(model_name, device=device, download_root=model_dir, compute_type=compute_type)
            del model  # Free memory immediately
            
        elif spec.source == "openvino":
            from modules.OpenVINOWhisper import OpenVINOWhisperModel
            
            # Use quantization from spec if provided, otherwise use compute_type arg
            final_compute_type = spec.quantization if spec.quantization else compute_type
            model = OpenVINOWhisperModel(model_name, device=device, download_root=model_dir, compute_type=final_compute_type)
            del model  # Free memory immediately
        
        else:
            raise ValueError(f"Unknown source: {spec.source}")
        
        if model_exists:
            print(f" {Fore.GREEN}[OK]{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}  → Download complete!{Style.RESET_ALL} {Fore.GREEN}[OK]{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f" {Fore.RED}[FAIL]{Style.RESET_ALL}")
        print(f"{Fore.RED}Error:{Style.RESET_ALL} {str(e)}")
        return False


def preload_models(preload_spec: str, model_dir: str = "models", device: str = "cuda", compute_type: str = "default") -> Tuple[int, int]:
    """
    Preload multiple models based on specification string.
    
    Args:
        preload_spec: Preload specification (e.g., "whisper:1gb+2gb,faster:1gb.en")
        model_dir: Root directory for model storage
        device: Device to use for loading
        compute_type: Compute type for FasterWhisper/OpenVINO
    
    Returns:
        Tuple[int, int]: (successful_count, total_count)
    """
    try:
        # Parse specification
        models = parse_preload_spec(preload_spec)
        
        if not models:
            print(f"{Fore.YELLOW}No models specified for preloading.{Style.RESET_ALL}")
            return (0, 0)
        
        # Display summary
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'  Model Preloading Started':^50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total models to preload: {len(models)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Model directory: {model_dir}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Device: {device}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Compute type: {compute_type}{Style.RESET_ALL}")
        print()
        
        # Preload each model
        successful = 0
        for i, model_spec in enumerate(models, 1):
            print(f"{Fore.CYAN}[{i}/{len(models)}]{Style.RESET_ALL} ", end='')
            if preload_model(model_spec, model_dir, device, compute_type):
                successful += 1
        
        # Summary
        print()
        if successful == len(models):
            print(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'  All Models Preloaded Successfully!':^50}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}{'='*50}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'  Model Preloading Completed with Errors':^50}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*50}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}Success: {successful}/{len(models)}{Style.RESET_ALL}")
        if successful < len(models):
            print(f"{Fore.YELLOW}Failed: {len(models) - successful}{Style.RESET_ALL}")
        print()
        
        return (successful, len(models))
        
    except ValueError as e:
        print(f"{Fore.RED}Error parsing preload specification:{Style.RESET_ALL} {str(e)}")
        print(f"{Fore.YELLOW}Format:{Style.RESET_ALL} source:size[.variant][+size.variant,...][,source:size...]")
        print(f"{Fore.YELLOW}Example:{Style.RESET_ALL} whisper:1gb+2gb.en,faster:1gb,openvino:1gb.int8")
        return (0, 0)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error during preloading:{Style.RESET_ALL} {str(e)}")
        return (0, 0)


# ---------------------------------------------------------------------------
# Demucs model preloading
#
# Demucs ships its model zoo as a set of checkpoints named <sig>-<checksum>.th
# plus small yaml "bag" files that group checkpoints into usable models (a bag
# can blend several checkpoints). The app consumes them from a local repo folder
# (<model_dir>/demucs) via demucs --repo, so preloading demucs means writing the
# checkpoints and bag yamls into that folder in exactly the layout demucs
# expects. Existing files are verified against the checksum embedded in their
# name and are never overwritten or deleted.
# ---------------------------------------------------------------------------

DEMUCS_ROOT_URL = "https://dl.fbaipublicfiles.com/demucs/"

DEMUCS_BAG_NAMES = (
    'htdemucs', 'htdemucs_ft', 'htdemucs_6s', 'hdemucs_mmi', 'mdx', 'mdx_q',
    'mdx_extra', 'mdx_extra_q', 'repro_mdx_a', 'repro_mdx_a_hybrid_only',
    'repro_mdx_a_time_only',
)

# Fallback registry mirroring demucs 4.0.1's remote/files.txt, used when the
# installed demucs package data cannot be located.
DEMUCS_FALLBACK_FILES = (
    ("mdx_final/", "0d19c1c6-0f06f20e.th"),
    ("mdx_final/", "5d2d6c55-db83574e.th"),
    ("mdx_final/", "7d865c68-3d5dd56b.th"),
    ("mdx_final/", "7ecf8ec1-70f50cc9.th"),
    ("mdx_final/", "a1d90b5c-ae9d2452.th"),
    ("mdx_final/", "c511e2ab-fe698775.th"),
    ("mdx_final/", "cfa93e08-61801ae1.th"),
    ("mdx_final/", "e51eebcc-c1b80bdd.th"),
    ("mdx_final/", "6b9c2ca1-3fd82607.th"),
    ("mdx_final/", "b72baf4e-8778635e.th"),
    ("mdx_final/", "42e558d4-196e0e1b.th"),
    ("mdx_final/", "305bc58f-18378783.th"),
    ("mdx_final/", "14fc6a69-a89dd0ee.th"),
    ("mdx_final/", "464b36d7-e5a9386e.th"),
    ("mdx_final/", "7fd6ef75-a905dd85.th"),
    ("mdx_final/", "83fc094f-4a16d450.th"),
    ("mdx_final/", "1ef250f1-592467ce.th"),
    ("mdx_final/", "902315c2-b39ce9c9.th"),
    ("mdx_final/", "9a6b4851-03af0aa6.th"),
    ("mdx_final/", "fa0cb7f9-100d8bf4.th"),
    ("hybrid_transformer/", "955717e8-8726e21a.th"),
    ("hybrid_transformer/", "f7e0c4bc-ba3fe64a.th"),
    ("hybrid_transformer/", "d12395a8-e57c48e6.th"),
    ("hybrid_transformer/", "92cfc3b6-ef3bcb9c.th"),
    ("hybrid_transformer/", "04573f0d-f3cf25b2.th"),
    ("hybrid_transformer/", "75fc33f5-1941ce65.th"),
    ("hybrid_transformer/", "5c90dfd2-34c22ccb.th"),
)

DEMUCS_FALLBACK_BAGS = {
    "htdemucs": {"models": ["955717e8"]},
    "htdemucs_ft": {"models": ["f7e0c4bc", "d12395a8", "92cfc3b6", "04573f0d"],
                    "weights": [[1., 0., 0., 0.], [0., 1., 0., 0.], [0., 0., 1., 0.], [0., 0., 0., 1.]]},
    "htdemucs_6s": {"models": ["5c90dfd2"]},
    "hdemucs_mmi": {"models": ["75fc33f5"], "segment": 44},
    "mdx": {"models": ["0d19c1c6", "7ecf8ec1", "c511e2ab", "7d865c68"],
            "weights": [[1., 1., 0., 0.], [0., 1., 0., 0.], [1., 0., 1., 1.], [1., 0., 1., 1.]], "segment": 44},
    "mdx_q": {"models": ["6b9c2ca1", "b72baf4e", "42e558d4", "305bc58f"],
              "weights": [[1., 1., 0., 0.], [0., 1., 0., 0.], [1., 0., 1., 1.], [1., 0., 1., 1.]], "segment": 44},
    "mdx_extra": {"models": ["e51eebcc", "a1d90b5c", "5d2d6c55", "cfa93e08"], "segment": 44},
    "mdx_extra_q": {"models": ["83fc094f", "464b36d7", "14fc6a69", "7fd6ef75"], "segment": 44},
    "repro_mdx_a": {"models": ["9a6b4851", "1ef250f1", "fa0cb7f9", "902315c2"], "segment": 44},
    "repro_mdx_a_hybrid_only": {"models": ["fa0cb7f9", "902315c2", "fa0cb7f9", "902315c2"], "segment": 44},
    "repro_mdx_a_time_only": {"models": ["9a6b4851", "9a6b4851", "1ef250f1", "1ef250f1"], "segment": 44},
}


def _demucs_package_dir() -> Optional[Path]:
    """Locate the installed demucs package folder without importing it."""
    try:
        import importlib.util
        spec = importlib.util.find_spec('demucs')
        if spec and getattr(spec, 'submodule_search_locations', None):
            return Path(list(spec.submodule_search_locations)[0])
    except Exception:
        pass
    return None


def _demucs_registry():
    """
    Build the demucs model registry.

    Returns a tuple (files, bags, bag_sources):
      files:       {signature: download url}
      bags:        {bag name: [signatures]}
      bag_sources: {bag name: yaml text to write into the repo folder}

    Reads the registry from the installed demucs package data when available,
    otherwise falls back to the built-in copy for demucs 4.0.1.
    """
    files: Dict[str, str] = {}
    bags: Dict[str, list] = {}
    bag_sources: Dict[str, str] = {}

    package_dir = _demucs_package_dir()
    if package_dir is not None:
        remote_dir = package_dir / 'remote'
        try:
            root = ''
            for line in (remote_dir / 'files.txt').read_text(encoding='utf-8').split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('root:'):
                    root = line.split(':', 1)[1].strip()
                    continue
                signature = line.split('-', 1)[0]
                files[signature] = DEMUCS_ROOT_URL + root + line

            import yaml
            for bag_file in sorted(remote_dir.glob('*.yaml')):
                data = yaml.safe_load(bag_file.read_text(encoding='utf-8'))
                if isinstance(data, dict) and data.get('models'):
                    bags[bag_file.stem] = list(data['models'])
                    bag_sources[bag_file.stem] = bag_file.read_text(encoding='utf-8')
        except Exception:
            files, bags, bag_sources = {}, {}, {}

    if not files or not bags:
        files = {
            name.split('-', 1)[0]: DEMUCS_ROOT_URL + root + name
            for root, name in DEMUCS_FALLBACK_FILES
        }
        bags = {name: list(data['models']) for name, data in DEMUCS_FALLBACK_BAGS.items()}
        bag_sources = {name: _format_demucs_bag_yaml(name) for name in bags}

    return files, bags, bag_sources


def _format_demucs_bag_yaml(name: str) -> str:
    """Render fallback bag data as yaml text in the layout demucs expects."""
    data = DEMUCS_FALLBACK_BAGS[name]
    lines = [f"models: {data['models']}"]
    if 'weights' in data:
        lines.append(f"weights: {data['weights']}")
    if 'segment' in data:
        lines.append(f"segment: {data['segment']}")
    return "\n".join(lines) + "\n"


def _file_sha256(path: Path) -> str:
    """Hash a file in chunks and return the hex digest."""
    from hashlib import sha256
    digest = sha256()
    with open(path, 'rb') as handle:
        while True:
            buffer = handle.read(2 ** 20)
            if not buffer:
                break
            digest.update(buffer)
    return digest.hexdigest()


def _download_demucs_checkpoint(url: str, dest: Path, checksum: str) -> bool:
    """
    Stream one checkpoint into place with progress output.

    The download goes to a temporary <name>.th.part file that is renamed to the
    final name only after its checksum matches, so a partial or corrupt download
    never replaces real content and an interrupted run leaves nothing behind.
    """
    import urllib.request

    part_path = Path(str(dest) + '.part')
    try:
        with urllib.request.urlopen(url, timeout=60) as source, open(part_path, 'wb') as output:
            total = int(source.headers.get('Content-Length') or 0)
            done = 0
            shown = -1
            while True:
                buffer = source.read(1024 * 512)
                if not buffer:
                    break
                output.write(buffer)
                done += len(buffer)
                if total:
                    percent = int(done * 100 / total)
                    if percent >= shown + 10 or percent == 100:
                        print(f"\r    {dest.name}: {percent}%", end='', flush=True)
                        shown = percent
        if shown >= 0:
            print()

        actual = _file_sha256(part_path)[:len(checksum)]
        if actual != checksum:
            print(f"{Fore.RED}    {dest.name}: checksum mismatch after download "
                  f"(expected {checksum}, got {actual}){Style.RESET_ALL}")
            return False

        part_path.rename(dest)
        return True
    finally:
        if part_path.exists():
            part_path.unlink()


def preload_demucs(bag_name: str, model_dir: str = "models") -> bool:
    """
    Download demucs models into <model_dir>/demucs using the local repo layout
    that `demucs --repo` expects: one <sig>-<checksum>.th checkpoint per file
    plus one yaml bag file per model.

    bag_name is either a single model name (see DEMUCS_BAG_NAMES) or 'all' for
    every model in the zoo. Existing checkpoints are verified against the
    checksum embedded in their file name and are never overwritten or deleted;
    only missing files are downloaded.
    """
    bag_name = bag_name.strip().lower()
    files, bags, bag_sources = _demucs_registry()

    if bag_name == 'all':
        bag_names = sorted(bags)
    elif bag_name in bags:
        bag_names = [bag_name]
    else:
        print(f"{Fore.RED}Unknown demucs model '{bag_name}'. "
              f"Available: {', '.join(sorted(bags))}, or 'all'{Style.RESET_ALL}")
        return False

    signatures: List[str] = []
    seen = set()
    for name in bag_names:
        for signature in bags[name]:
            if signature not in seen:
                seen.add(signature)
                signatures.append(signature)

    target_dir = Path(os.path.join(model_dir, 'demucs'))
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"{Fore.CYAN}[Preload]{Style.RESET_ALL} demucs:{bag_name} -> {target_dir} "
          f"({len(bag_names)} bag(s), {len(signatures)} checkpoint(s))")

    failures = 0

    # Stage the bag yaml files first so downloaded checkpoints are usable immediately.
    for name in bag_names:
        bag_file = target_dir / f"{name}.yaml"
        if bag_file.exists():
            continue
        try:
            bag_file.write_text(bag_sources[name], encoding='utf-8')
            print(f"    {name}.yaml written")
        except Exception as exc:
            print(f"{Fore.RED}    could not write {name}.yaml: {exc}{Style.RESET_ALL}")
            failures += 1

    for signature in signatures:
        url = files.get(signature)
        if not url:
            print(f"{Fore.RED}    no download URL for signature {signature}{Style.RESET_ALL}")
            failures += 1
            continue

        filename = url.rsplit('/', 1)[-1]
        checkpoint = target_dir / filename
        parts = checkpoint.stem.split('-', 1)
        if len(parts) != 2 or not parts[1]:
            print(f"{Fore.RED}    unexpected checkpoint name '{filename}'{Style.RESET_ALL}")
            failures += 1
            continue
        checksum = parts[1]

        if checkpoint.exists():
            actual = _file_sha256(checkpoint)[:len(checksum)]
            if actual == checksum:
                print(f"    {filename}: {Fore.GREEN}[OK, verified]{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}    {filename}: CHECKSUM MISMATCH (expected {checksum}, got {actual}). "
                      f"Delete the file and run again to re-download it.{Style.RESET_ALL}")
                failures += 1
            continue

        try:
            if _download_demucs_checkpoint(url, checkpoint, checksum):
                print(f"    {filename}: {Fore.GREEN}[downloaded]{Style.RESET_ALL}")
            else:
                failures += 1
        except Exception as exc:
            print(f"{Fore.RED}    {filename}: download failed: {exc}{Style.RESET_ALL}")
            failures += 1

    if failures:
        print(f"{Fore.YELLOW}    demucs: {len(signatures) - failures}/{len(signatures)} "
              f"checkpoints OK, {failures} failed{Style.RESET_ALL}")
        return False

    print(f"{Fore.GREEN}    demucs: all {len(signatures)} checkpoints present and verified{Style.RESET_ALL}")
    return True


def generate_all_models_spec(device: str = "cuda") -> str:
    """
    Generate a preload specification string that includes all possible models.

    Args:
        device: Device being used ('cuda', 'cpu', etc.) - affects which sources to include

    Returns:
        str: Comprehensive preload specification covering all sources, sizes, and variants
    """
    sources = ['whisper', 'faster']
    sizes = ['1gb', '2gb', '3gb', '6gb', '7gb', '11gb-v2', '11gb-v3']

    # English-only variants are available for these sizes
    english_sizes = ['1gb', '2gb', '3gb', '6gb']

    # Only include OpenVINO if device is CPU (OpenVINO doesn't support CUDA)
    if device.lower() == 'cpu':
        sources.append('openvino')

    source_specs = []

    for source in sources:
        size_specs = []

        for size in sizes:
            # Add base size
            size_specs.append(size)

            # Add English variant if available for this size
            if size in english_sizes:
                size_specs.append(f"{size}.en")

            # Add quantization for OpenVINO
            if source == 'openvino':
                size_specs.append(f"{size}.int8")

        # Join sizes for this source
        source_specs.append(f"{source}:{'+'.join(size_specs)}")

    # Join all sources
    spec = ','.join(source_specs)

    # Demucs vocal isolation models are device independent, always include them.
    spec += ",demucs:all"
    return spec


def validate_preload_spec(spec: str) -> Tuple[bool, str]:
    """
    Validate preload specification without actually loading models.

    Args:
        spec: Preload specification string

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        models = parse_preload_spec(spec)

        if not models:
            return (False, "No models specified")

        # Validate each model
        for model in models:
            try:
                model.to_model_name()  # This will raise ValueError if invalid
            except ValueError as e:
                return (False, str(e))

        return (True, f"Valid specification: {len(models)} model(s)")

    except ValueError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    """Test/demo functionality when run directly."""
    
    print("Model Preloader Test\n")
    
    # Test parsing
    test_specs = [
        "whisper:1gb",
        "faster:1gb.en",
        "openvino:1gb.int8",
        "whisper:1gb+2gb.en",
        "whisper:1gb,faster:2gb,openvino:1gb.int8",
        "faster:1gb+2gb.en+3gb",
        "demucs:all",
        "demucs:htdemucs_ft",
    ]
    
    print("Testing specification parsing:\n")
    for spec in test_specs:
        print(f"Input:  {spec}")
        is_valid, message = validate_preload_spec(spec)
        if is_valid:
            models = parse_preload_spec(spec)
            print(f"Result: {Fore.GREEN}[OK]{Style.RESET_ALL} {message}")
            for model in models:
                print(f"  - {model.source}:{model.to_model_name()}")
        else:
            print(f"Result: {Fore.RED}[FAIL]{Style.RESET_ALL} {message}")
        print()