"""Modern About screen presentation for Synthalingua."""

from __future__ import annotations

import os
import re
import shutil
import sys
import textwrap
import time
from typing import Sequence, Tuple

from colorama import Fore, Style, init

from modules.version_checker import version


init(autoreset=True)

USE_COLOR = sys.stdout.isatty()
MIN_WIDTH = 78
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
DEFAULT_LINE_DELAY = 0.03
HEADER_LINE_DELAY = 0.05
RULE_LINE_DELAY = 0.015
BULLET_LINE_DELAY = 0.04


def animated_print(text: str = "", delay: float = DEFAULT_LINE_DELAY) -> None:
    """Print a line and pause briefly for animation."""

    print(text)
    time.sleep(max(delay, 0))


def strip_ansi(text: str) -> str:
    """Return text with ANSI escape codes removed."""

    return ANSI_PATTERN.sub("", text)


def stylize(text: str, *codes: str) -> str:
    """Wrap text in ANSI codes when supported."""

    if not USE_COLOR or not codes:
        return text
    return f"{''.join(codes)}{text}{Style.RESET_ALL}"


def pad_visible(text: str, width: int) -> str:
    """Pad string accounting for visible characters only."""

    visible = len(strip_ansi(text))
    return text + " " * max(width - visible, 0)


def clear_console() -> None:
    """Clear the terminal for a clean presentation."""

    os.system('cls' if os.name == 'nt' else 'clear')


def terminal_width(default: int = MIN_WIDTH) -> int:
    """Return terminal width, enforcing a sensible minimum."""

    try:
        width = shutil.get_terminal_size().columns
    except OSError:
        width = default
    return max(width, default)


def print_centered(text: str, width: int) -> None:
    """Print text centered within the visible width."""

    padding = max((width - len(strip_ansi(text))) // 2, 0)
    animated_print(" " * padding + text)


def draw_rule(width: int, accent: str, heavy: bool = False) -> None:
    """Render a horizontal rule using light or heavy characters."""

    char = "═" if heavy else "─"
    animated_print(stylize(char * width, accent), RULE_LINE_DELAY)


def section_header(title: str, width: int, accent: str) -> None:
    """Print a centered section header with matching rules."""

    animated_print("", RULE_LINE_DELAY)
    draw_rule(width, accent, heavy=False)
    print_centered(stylize(title.upper(), accent, Style.BRIGHT), width)
    draw_rule(width, accent, heavy=False)


def fact_line(label: str, value: str, width: int) -> None:
    """Render a label/value pair with wrapping support."""

    bullet = stylize("▸", Fore.CYAN, Style.BRIGHT)
    label_text = stylize(label, Style.BRIGHT)
    lead = f" {bullet} {label_text}: "
    wrap_width = max(width - len(strip_ansi(lead)) - 4, 30)
    wrapped = textwrap.wrap(value, wrap_width) or [""]

    animated_print(f"{lead}{wrapped[0]}", BULLET_LINE_DELAY)
    indent = " " * len(strip_ansi(lead))
    for continuation in wrapped[1:]:
        animated_print(f"{indent}{continuation}", BULLET_LINE_DELAY)


def feature_grid(features: Sequence[str], width: int) -> None:
    """Display features in one or two columns based on width."""

    accent = stylize("•", Fore.MAGENTA, Style.BRIGHT)
    if width < 96 or len(features) <= 4:
        for feature in features:
            animated_print(f"   {accent} {feature}", BULLET_LINE_DELAY)
        return

    col_width = (width - 6) // 2
    rows = (len(features) + 1) // 2
    left = features[:rows]
    right = features[rows:]

    for idx in range(rows):
        left_text = f"{accent} {left[idx]}" if idx < len(left) else ""
        right_text = f"{accent} {right[idx]}" if idx < len(right) else ""
        animated_print(
            "   " + pad_visible(left_text, col_width) + ("   " + right_text if right_text else ""),
            BULLET_LINE_DELAY,
        )


def contributor_block(entries: Sequence[Tuple[str, str, str]], width: int) -> None:
    """Render contributor credits with optional roles."""

    for name, url, role in entries:
        animated_print(f" {stylize('▹', Fore.CYAN)} {stylize(name, Fore.CYAN, Style.BRIGHT)}", BULLET_LINE_DELAY)
        if role:
            animated_print(f"    {stylize('Role:', Fore.LIGHTWHITE_EX)} {role}", BULLET_LINE_DELAY)
        animated_print(f"    {stylize('Link:', Fore.LIGHTWHITE_EX)} {url}", BULLET_LINE_DELAY)
        animated_print("", BULLET_LINE_DELAY)


def animated_prompt(message: str, width: int, delay: float = 0.015) -> None:
    """Display a centered prompt with a subtle typewriter effect."""

    padding = max((width - len(message)) // 2, 0)
    print(" " * padding, end="")
    for char in message:
        print(char, end="", flush=True)
        time.sleep(delay)
    animated_print("", DEFAULT_LINE_DELAY)


def contributors(ScriptCreator: str, GitHubRepo: str) -> None:
    """Render the modern about screen and exit afterwards."""

    clear_console()
    width = terminal_width()

    headline = stylize("SYNTHALINGUA", Style.BRIGHT)
    tagline = "Real-time audio translation that keeps creators in sync."

    draw_rule(width, Fore.CYAN, heavy=True)
    print_centered(headline, width)
    print_centered(stylize(tagline, Fore.LIGHTWHITE_EX), width)
    draw_rule(width, Fore.CYAN, heavy=True)

    section_header("Project Snapshot", width, Fore.LIGHTBLUE_EX)
    snapshot = [
        ("Version", f"v{version}"),
        ("Created by", ScriptCreator),
        ("License", "AGPLv3 (GNU Affero General Public License v3)"),
        ("Repository", GitHubRepo),
        ("Powered by", "OpenAI Whisper"),
        ("Highlights", "Live transcription, translation, and subtitle generation in one toolkit"),
    ]
    for label, value in snapshot:
        fact_line(label, value, width)

    section_header("Why Creators Love Synthalingua", width, Fore.MAGENTA)
    feature_grid(
        [
            "Real-time transcription tuned for streams and events",
            "Instant multi-language translation with smart defaults",
            "Microphone, HLS, and file-based workflows supported side-by-side",
            "Web dashboard (with optional HTTPS) for remote teams",
            "Flexible filtering, blocklists, and subtitle formatting",
            "Discord webhook notifications and update awareness built-in",
        ],
        width,
    )

    section_header("Contributors & Acknowledgments", width, Fore.LIGHTCYAN_EX)
    contributor_block(
        [
            ("@DaniruKun", "https://watsonindustries.live", ""),
            ("[Expletive Deleted]", "https://evitelpxe.neocities.org", ""),
            ("YuumiPie", "https://github.com/YuumiPie", ""),
            ("OpenAI Team", "https://openai.com", "🧠 Whisper Models"),
            ("SYSTRAN", "https://www.systransoft.com", "🧠 Faster Whisper backend"),
            ("OpenVINO", "https://github.com/openvinotoolkit/openvino", "🧠 OpenVINO Whisper backend"),
            ("Community", "GitHub Issues & PRs", "🤝 Support"),
        ],
        width,
    )

    print()
    closing = stylize("Breaking language barriers in real time.", Fore.LIGHTCYAN_EX, Style.BRIGHT)
    print_centered(closing, width)
    animated_prompt("Press Enter to continue.", width)

    try:
        input()
    except KeyboardInterrupt:
        pass

    sys.exit()