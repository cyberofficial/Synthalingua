"""
🎨 Enhanced About Module for Synthalingua 🎨

This module provides a visually stunning display of project information,
featuring ASCII art, gradient colors, and modern terminal styling.
Displays creator info, license, repository link, and contributors
with eye-catching visual effects.
"""

from colorama import Fore, Back, Style, init
import sys
import time
import os

# Initialize colorama for Windows compatibility
init(autoreset=True)

def print_gradient_text(text, colors):
    """Print text with gradient-like color effect."""
    color_cycle = colors * (len(text) // len(colors) + 1)
    for i, char in enumerate(text):
        print(color_cycle[i % len(colors)] + char, end='')
    print(Style.RESET_ALL)

def print_banner():
    """Display the awesome ASCII art banner."""
    banner = f"""
{Fore.CYAN}╔════════════════════════════════════════════════════════════════════════════════════════════════╗
{Fore.CYAN}║                                                                                                ║
{Fore.MAGENTA}║  ███████╗██╗   ██╗███╗   ██╗████████╗██╗  ██╗ █████╗ ██╗     ██╗███╗   ██╗ ██████╗ ██╗   ██╗ █████╗  ║
{Fore.MAGENTA}║  ██╔════╝╚██╗ ██╔╝████╗  ██║╚══██╔══╝██║  ██║██╔══██╗██║     ██║████╗  ██║██╔════╝ ██║   ██║██╔══██╗ ║
{Fore.BLUE}║  ███████╗ ╚████╔╝ ██╔██╗ ██║   ██║   ███████║███████║██║     ██║██╔██╗ ██║██║  ███╗██║   ██║███████║ ║
{Fore.BLUE}║  ╚════██║  ╚██╔╝  ██║╚██╗██║   ██║   ██╔══██║██╔══██║██║     ██║██║╚██╗██║██║   ██║██║   ██║██╔══██║ ║
{Fore.GREEN}║  ███████║   ██║   ██║ ╚████║   ██║   ██║  ██║██║  ██║███████╗██║██║ ╚████║╚██████╔╝╚██████╔╝██║  ██║ ║
{Fore.GREEN}║  ╚══════╝   ╚═╝   ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ║
{Fore.CYAN}║                                                                                                ║
{Fore.CYAN}║                              🎤 Real-Time Audio Translation 🌐                                 ║
{Fore.CYAN}║                                                                                                ║
{Fore.CYAN}╚════════════════════════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_section_header(title, icon="✨"):
    """Print a stylized section header."""
    line = "─" * (len(title) + 6)
    print(f"\n{Fore.YELLOW}┌{line}┐")
    print(f"│ {icon} {Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL} {Fore.YELLOW}{icon} │")
    print(f"└{line}┘{Style.RESET_ALL}")

def print_info_line(label, value, color=Fore.GREEN):
    """Print a formatted information line."""
    print(f"  {Fore.CYAN}▶ {Style.BRIGHT}{label}:{Style.RESET_ALL} {color}{value}{Style.RESET_ALL}")

def print_loading_effect(text, delay=0.05):
    """Print text with a typewriter effect."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def contributors(ScriptCreator, GitHubRepo):
    """
    Display project information and contributor credits with enhanced visuals.

    Features:
    - ASCII art banner
    - Gradient text effects
    - Structured information display
    - Modern terminal styling
    - Animated loading effects

    Args:
        ScriptCreator (str): Name of the project creator
        GitHubRepo (str): URL of the project's GitHub repository

    Note:
        This function calls sys.exit() after displaying the information.
    """
    # Clear screen for better presentation
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Display banner
    print_banner()
      # Project Information Section
    print_section_header("PROJECT INFORMATION", "🚀")
    print_info_line("Created by", ScriptCreator, Fore.MAGENTA)
    print_info_line("License", "AGPLv3 (GNU Affero General Public License v3)", Fore.GREEN)
    print_info_line("Repository", GitHubRepo, Fore.BLUE)
    print_info_line("Based on", "OpenAI Whisper", Fore.YELLOW)
    print_info_line("Whisper URL", "https://github.com/openai/whisper", Fore.YELLOW)
    
    # Features Section
    print_section_header("KEY FEATURES", "⚡")
    features = [
        "🎙️  Real-time audio transcription",
        "🌍  Multi-language translation support",
        "🔊  Live microphone input processing",
        "📁  Audio file transcription",
        "🌐  Web interface for easy access",
        "⚙️   Customizable settings and filters"
    ]
    
    for feature in features:
        print(f"  {Fore.GREEN}{feature}{Style.RESET_ALL}")
        time.sleep(0.1)
    
    # Contributors Section
    print_section_header("CONTRIBUTORS & ACKNOWLEDGMENTS", "👥")
    
    contributors_list = [
        ("@DaniruKun", "https://watsonindustries.live", ""),
        ("[Expletive Deleted]", "https://evitelpxe.neocities.org", ""),
        ("OpenAI Team", "https://openai.com", "🧠 Whisper Models"),
        ("Community", "GitHub Issues & PRs", "🤝 Support")
    ]
    for name, url, role in contributors_list:
        print(f"  {Fore.CYAN}▶ {Style.BRIGHT}{name}{Style.RESET_ALL}")
        if role:  # Only show role if it's not empty
            print(f"    {Fore.WHITE}Role: {Fore.YELLOW}{role}{Style.RESET_ALL}")
        print(f"    {Fore.WHITE}Link: {Fore.BLUE}{url}{Style.RESET_ALL}")
        print()
    
    # Footer
    print_section_header("THANK YOU FOR USING SYNTHALINGUA!", "🎉")
    
    # Animated closing message
    closing_colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    print_gradient_text("      Breaking language barriers, one word at a time! 🌟", closing_colors)
    
    print(f"\n{Fore.WHITE}{Style.DIM}Press any key to continue...{Style.RESET_ALL}")
    
    # Wait for user input before exiting
    try:
        input()
    except KeyboardInterrupt:
        pass
    
    sys.exit()

print("About Module Loaded")