"""
Model Preloader Module

This module handles preloading and caching of Whisper models for Synthalingua.
Supports multiple model sources (Whisper, FasterWhisper, OpenVINO) with various
configurations including English-only variants and quantization options.

Features:
- Parse complex preload specifications (e.g., "whisper:1gb+2gb.en,faster:3gb")
- Download and cache models before main application runs
- Support for multiple model sources and variants
- Batch preloading with progress tracking
- Validation of model specifications

Usage:
    from modules.model_preloader import preload_models
    
    preload_models("whisper:1gb+2gb,faster:1gb.en", model_dir="models", device="cuda")
"""

import os
import sys
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
            str: Model name (e.g., 'tiny', 'base.en', 'large-v3')
        """
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
        valid_sources = ['whisper', 'faster', 'openvino']
        if source not in valid_sources:
            raise ValueError(f"Invalid source '{source}': must be one of {valid_sources}")
        
        # Split by + to get multiple sizes for same source
        size_specs = [s.strip() for s in sizes_spec.split('+')]
        
        for size_spec in size_specs:
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
        model_name = spec.to_model_name()
        
        # Check if model already exists
        model_exists = False
        if spec.source == "whisper":
            model_path = os.path.join(model_dir, "Whisper", f"{model_name}.pt")
            model_exists = os.path.exists(model_path)
        elif spec.source == "faster":
            model_path = os.path.join(model_dir, "FasterWhisper", f"models--Systran--faster-whisper-{model_name}")
            model_exists = os.path.exists(model_path)
        elif spec.source == "openvino":
            model_path = os.path.join(model_dir, "OpenVINO", model_name)
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
