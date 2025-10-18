"""
SRT file fixing utilities for Synthalingua.

This module provides functionality to fix SRT subtitle files with incorrect
timestamp ordering by sorting subtitles chronologically.
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from colorama import Fore, Style


def fix_srt_file(srt_path: str) -> None:
    """
    Fix SRT file with incorrect timestamp ordering by sorting subtitles chronologically.
    
    Args:
        srt_path (str): Path to the SRT file to fix
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the file format is invalid
    """
    srt_file = Path(srt_path)
    if not srt_file.exists():
        raise FileNotFoundError(f"SRT file not found: {srt_path}")
    
    print(f"{Fore.CYAN}Fixing SRT file: {srt_path}{Style.RESET_ALL}")
    
    # Parse SRT file
    subtitles: List[Dict[str, Any]] = []
    current_subtitle: Dict[str, Any] = {}
    
    with open(srt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Parse subtitle number
        if line.isdigit():
            if current_subtitle:
                subtitles.append(current_subtitle)
            current_subtitle = {'number': int(line)}
            i += 1
            continue
        
        # Parse timestamp line
        timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', line)
        if timestamp_match:
            start_time_str, end_time_str = timestamp_match.groups()
            current_subtitle['start_time'] = start_time_str
            current_subtitle['end_time'] = end_time_str
            current_subtitle['start_seconds'] = _timestamp_to_seconds(start_time_str)
            current_subtitle['end_seconds'] = _timestamp_to_seconds(end_time_str)
            i += 1
            continue
        
        # Parse text content
        if 'text' not in current_subtitle:
            current_subtitle['text'] = []
        
        # Collect all text lines until next subtitle or end
        while i < len(lines) and lines[i].strip():
            current_subtitle['text'].append(lines[i].strip())
            i += 1
    
    # Add the last subtitle
    if current_subtitle:
        subtitles.append(current_subtitle)
    
    if not subtitles:
        raise ValueError(f"No valid subtitles found in {srt_path}")
    
    print(f"{Fore.CYAN}Found {len(subtitles)} subtitles{Style.RESET_ALL}")
    
    # Sort subtitles by start time
    sorted_subtitles = sorted(subtitles, key=lambda x: x['start_seconds'])
    
    # Create output filename
    output_path = srt_file.parent / f"{srt_file.stem}_repaired{srt_file.suffix}"
    
    # Write fixed SRT file
    with open(output_path, 'w', encoding='utf-8') as f:
        for idx, subtitle in enumerate(sorted_subtitles, 1):
            f.write(f"{idx}\n")
            f.write(f"{subtitle['start_time']} --> {subtitle['end_time']}\n")
            f.write('\n'.join(subtitle['text']) + '\n\n')
    
    print(f"{Fore.GREEN}Fixed SRT file saved as: {output_path}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Subtitles reordered chronologically{Style.RESET_ALL}")


def _timestamp_to_seconds(timestamp: str) -> float:
    """
    Convert SRT timestamp to seconds for sorting.
    
    Args:
        timestamp (str): Timestamp in format HH:MM:SS,mmm
        
    Returns:
        float: Time in seconds
    """
    hours, minutes, seconds = timestamp.split(':')
    seconds, milliseconds = seconds.split(',')
    
    total_seconds = (int(hours) * 3600 + 
                    int(minutes) * 60 + 
                    int(seconds) + 
                    int(milliseconds) / 1000)
    
    return total_seconds