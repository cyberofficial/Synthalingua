"""
Run manager for the Python UI (phase 2 of python_ui_plan.md).

Owns four things the web UI needs and the .NET wrapper never had:

1. Settings persistence in %APPDATA%\\Synthalingua\\settings.json (atomic write,
   unknown keys preserved).
2. argv and argparse.Namespace construction from those settings, reproducing
   CommandGenerator.vb semantics field for field.
3. A single-run state machine (idle / starting / running / stopping / stopped /
   error) with start, stop and status.
4. A 500 line log ring buffer, streamed to the browser over SocketIO as
   "run_log" events, with "run_state" events on every state change.

Importing this module has no side effects: no thread, no process, no file is
touched until a function is called.

How a run is executed
---------------------
A run is a child process launched with the argv this module builds, never an
in-process call. The reasons are in the task report: argparse would have to be
fed through sys.argv of the already-running server, and the caption path ends
in blocking input() prompts plus sys.exit(). A child process keeps the server
alive if the run dies and needs no edits to synthalingua.py.

Interactive prompts
-------------------
Input is never left closed (that would raise EOFError) and never left as a
terminal (that would hang forever). A feeder thread writes blank lines to the
child's stdin, so every input() returns an empty string immediately and the
unguarded prompts in sub_gen.py resolve to their default branch instead of
blocking the run.
"""

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

APP_DIR_NAME = "Synthalingua"
SETTINGS_FILE_NAME = "settings.json"

#: Emitted over SocketIO. Frozen by CONTRACT v1.
EVENT_RUN_LOG = "run_log"
EVENT_RUN_STATE = "run_state"

#: Size of the log ring buffer kept in memory.
LOG_BUFFER_MAX = 500

#: How many trailing lines /api/run/status returns.
LOG_TAIL_MAX = 20

#: Seconds a stopped child is given to exit before it is killed.
STOP_GRACE_SECONDS = 5.0
TASKKILL_TIMEOUT_SECONDS = 15.0

#: How many "1" answers the stdin feeder writes before switching to blank
#: lines. Covers the segmentation menu and the timeout recovery menu.
MENU_ANSWER_LINES = 8

#: Delay between stdin responses, so a menu answer cannot arrive before the
#: prompt that should consume it.
STDIN_FEED_INTERVAL = 0.2

#: The three modes the UI exposes.
MODES = ("captions", "hls", "mic")

#: Keys that are UI state only and never become argv.
UI_KEY_PREFIX = "ui_"

#: CLI option names without leading dashes, exactly as CONTRACT v1 lists them.
CLI_KEYS = (
    "makecaptions", "ram", "ramforce", "model_source", "model_dir", "fp16",
    "language", "stream_language", "translate", "stream_translate",
    "transcribe", "target_language", "stream_transcribe", "device", "stream",
    "cookies", "remote_hls_password_id", "remote_hls_password", "auto_hls",
    "selectsource", "stream_original_text", "stream_chunks", "paddedaudio",
    "microphone_enabled", "energy_threshold", "mic_calibration_time",
    "record_timeout", "phrase_timeout", "set_microphone", "mic_chunk_size",
    "file_input", "file_output", "file_output_name", "print_srt_to_console",
    "silent_detect", "silent_threshold", "silent_duration", "intelligent_mode",
    "timeout", "word_timestamps", "subtype", "substyle", "adaptive_batch",
    "batchjobsize", "cpu_batches", "max_cpu_time", "batchmode",
    "isolate_vocals", "demucs_model", "ignorelist",
    "condition_on_previous_text", "discord_webhook", "auto_blocklist",
    "debug", "portnumber", "https", "serverip",
)

#: Defaults mirror modules/parser_args.py so a preview is honest about what the
#: CLI would do when a key is absent. None means "not passed".
DEFAULTS = {
    "mode": "captions",
    "makecaptions": True,
    "ram": "2gb",
    "ramforce": False,
    "model_source": "whisper",
    "model_dir": "models",
    "fp16": False,
    "language": None,
    "stream_language": None,
    "translate": False,
    "stream_translate": False,
    "transcribe": False,
    "target_language": None,
    "stream_transcribe": None,
    "device": "cuda",
    "stream": None,
    "cookies": None,
    "remote_hls_password_id": None,
    "remote_hls_password": None,
    "auto_hls": False,
    "selectsource": None,
    "stream_original_text": False,
    "stream_chunks": 5,
    "paddedaudio": 0,
    "microphone_enabled": None,
    "energy_threshold": 100,
    "mic_calibration_time": None,
    "record_timeout": 1,
    "phrase_timeout": 1,
    "set_microphone": None,
    "mic_chunk_size": 1,
    "file_input": None,
    "file_output": None,
    "file_output_name": None,
    "print_srt_to_console": False,
    "silent_detect": False,
    "silent_threshold": -35.0,
    "silent_duration": 0.5,
    "intelligent_mode": False,
    "timeout": 0,
    "word_timestamps": False,
    "subtype": None,
    "substyle": None,
    "adaptive_batch": False,
    "batchjobsize": 4,
    "cpu_batches": None,
    "max_cpu_time": 300,
    "batchmode": 1,
    "isolate_vocals": False,
    "demucs_model": "htdemucs",
    "demucs_jobs": None,
    "ignorelist": None,
    "condition_on_previous_text": False,
    "discord_webhook": None,
    "auto_blocklist": False,
    "debug": False,
    "portnumber": None,
    "https": None,
    "serverip": "127.0.0.1",
    # UI-only defaults (never become argv).
    "ui_disclaimer_accepted": False,
    "ui_caption_streams": {"original": True, "translated": True, "transcribed": True},
    "ui_caption_font": "Segoe UI",
    "ui_caption_font_size": 28,
    "ui_caption_color": "#ffffff",
    "ui_caption_background": "#000000",
    "ui_caption_alignment": "bottom-center",
    "ui_caption_rtl": False,
    "ui_caption_pinned": False,
    "ui_last_tab": "captions",
}

#: Flag options that take no value.
FLAG_KEYS = (
    "ramforce", "fp16", "translate", "stream_translate", "transcribe",
    "auto_hls", "stream_original_text", "print_srt_to_console", "silent_detect",
    "intelligent_mode", "word_timestamps", "adaptive_batch",
    "condition_on_previous_text", "auto_blocklist", "debug",
)

#: Option keys that are ints, used to coerce incoming JSON numbers/strings.
INT_KEYS = (
    "stream_chunks", "energy_threshold", "mic_calibration_time",
    "record_timeout", "phrase_timeout", "mic_chunk_size", "timeout",
    "batchjobsize", "cpu_batches", "max_cpu_time", "batchmode", "paddedaudio",
    "portnumber", "https",
)

#: Option keys that are floats.
FLOAT_KEYS = ("silent_threshold", "silent_duration")

#: Option keys that must be one of a fixed set.
CHOICE_KEYS = {
    "model_source": ("whisper", "fasterwhisper", "openvino"),
    "device": ("cuda", "cpu", "auto", "intel-igpu", "intel-dgpu", "intel-npu"),
    "subtype": ("burn", "embed"),
    "ram": ("1gb", "2gb", "3gb", "6gb", "7gb", "11gb-v2", "11gb-v3"),
    "demucs_model": ("htdemucs", "htdemucs_ft", "htdemucs_6s", "hdemucs_mmi",
                     "mdx", "mdx_extra", "mdx_q", "mdx_extra_q", "hdemucs",
                     "demucs"),
}

#: Demucs allowlist the wrapper enforced, kept so "DEFAULT" still means "let the
#: app choose" for old settings files.
DEMUCS_DEFAULT_SENTINEL = "DEFAULT"

_RUN_LOCK = threading.RLock()


# --------------------------------------------------------------------------
# Settings persistence
# --------------------------------------------------------------------------

def settings_path():
    """Absolute path of the settings file, creating its folder if needed."""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, APP_DIR_NAME)
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        pass
    return os.path.join(folder, SETTINGS_FILE_NAME)


def default_settings():
    """A fresh copy of the defaults (deep enough for the dict values used)."""
    out = {}
    for key, value in DEFAULTS.items():
        out[key] = dict(value) if isinstance(value, dict) else value
    return out


def _coerce(key, value):
    """Coerce one incoming value to the type parser_args.py expects.

    A value that cannot be parsed is passed through unchanged instead of being
    silently replaced with None. Dropping it is what let a port typo become
    "pick a free port"; keeping it means validate_settings() can reject it with
    a 400 while the settings file still shows what was actually sent. Empty and
    whitespace-only strings stay None, because that is how the UI clears a
    field.
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    if key in FLAG_KEYS:
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)
    if key == "batchjobsize":
        # parser_args.py:28 valid_batchjobsize is a FLOAT (0.1 to 12.0), so a
        # fractional size must survive; an integral value keeps its int form so
        # the emitted argv is unchanged for the pinned presets.
        if isinstance(value, bool):
            return value
        if isinstance(value, float):
            return value if not value.is_integer() else int(value)
        if isinstance(value, int):
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    if key in INT_KEYS:
        if isinstance(value, bool):
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    if key in FLOAT_KEYS:
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    return value


def merge_settings(base, patch):
    """Merge a partial settings object into base, preserving unknown keys.

    Unknown keys survive so a newer UI (or a hand edit) is never silently
    stripped by an older server.
    """
    if not isinstance(patch, dict):
        return dict(base)
    out = dict(base)
    for key, value in patch.items():
        if not isinstance(key, str):
            continue
        if key.startswith(UI_KEY_PREFIX) or key == "mode":
            out[key] = value
            continue
        out[key] = _coerce(key, value)
    return out


def load_settings():
    """Read settings.json, merged over the defaults. Never raises."""
    settings = default_settings()
    path = settings_path()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            settings = merge_settings(settings, data)
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        # A corrupt file must not take the UI down; defaults are used and the
        # next save rewrites it atomically.
        pass
    return settings


def save_settings(settings):
    """Persist settings atomically (temp file plus os.replace)."""
    path = settings_path()
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    tmp_path = os.path.join(folder, f".settings.{uuid.uuid4().hex}.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return path


# --------------------------------------------------------------------------
# argv construction (CommandGenerator.vb semantics)
# --------------------------------------------------------------------------

def resolve_mode(settings):
    """Return captions | hls | mic for a settings object."""
    explicit = settings.get("mode")
    if explicit in MODES:
        # An explicit mode still loses to an unambiguous source, so a stale
        # mode key can never produce an argv with no input.
        if explicit == "hls" and not settings.get("stream"):
            pass
        else:
            return explicit
    if settings.get("stream"):
        return "hls"
    if settings.get("microphone_enabled"):
        return "mic"
    return "captions"


def normalize_serverip(raw):
    """Port of CommandGenerator.NormalizeServerIp: sanitize or fall back."""
    default = "127.0.0.1"
    if raw is None:
        return default
    sanitized = str(raw).replace("_", "").replace(" ", "")
    if not sanitized:
        return default
    segments = [part for part in sanitized.split(".") if part != ""]
    if len(segments) != 4:
        return default
    normalized = []
    for segment in segments:
        if not segment.isdigit():
            return default
        value = int(segment)
        if value < 0 or value > 255:
            return default
        normalized.append(str(value))
    return ".".join(normalized)


def _flag(argv, name, value, default=None):
    """Append --name when value is set and differs from default."""
    if value is None:
        return
    if isinstance(value, bool):
        if value:
            argv.append(f"--{name}")
        return
    if default is not None and value == default:
        return
    if isinstance(value, str) and value == "":
        return
    argv.append(f"--{name}")
    argv.append(str(value))


def _flag_always(argv, name, value):
    """Append --name value whenever value is not None or False."""
    if value is None or value is False or value == "":
        return
    argv.append(f"--{name}")
    argv.append(str(value))


def _quote(token):
    """Quote one argv token the way CommandGenerator writes it into the bat."""
    if token == "":
        return '""'
    if any(ch in token for ch in ' \t"'):
        return '"' + token.replace('"', '\\"') + '"'
    return token


def arg_line(argv):
    """The display form (quoted) of argv, as the wrapper bat would contain it."""
    return " ".join(_quote(str(token)) for token in argv)


def build_argv(settings):
    """Build the CLI argv list for settings, matching CommandGenerator order.

    Order of blocks: ram, mode audio source, language, device, additional,
    model source. Web server flags sit inside the HLS and mic blocks, exactly
    where AppendWebServerSettings is called in the wrapper.
    """
    mode = resolve_mode(settings)
    argv = []

    # --- RAM -------------------------------------------------------------
    ram = settings.get("ram") or DEFAULTS["ram"]
    argv.append("--ram")
    argv.append(str(ram))
    if settings.get("ramforce"):
        argv.append("--ramforce")

    # --- Mode block ------------------------------------------------------
    if mode == "captions":
        _append_captions(argv, settings)
    elif mode == "hls":
        _append_hls(argv, settings)
    else:
        _append_mic(argv, settings)

    # --- Language --------------------------------------------------------
    prefix = "stream_" if mode == "hls" else ""
    language = settings.get(f"{prefix}language")
    if language and str(language) != "--Auto Detect--":
        argv.append(f"--{prefix}language")
        argv.append(str(language))

    if settings.get(f"{prefix}translate"):
        argv.append(f"--{prefix}translate")

    if mode == "hls":
        stream_transcribe = settings.get("stream_transcribe")
        if stream_transcribe:
            argv.append("--stream_transcribe")
            argv.append(str(stream_transcribe))
    else:
        if settings.get("transcribe"):
            argv.append("--transcribe")
            target = settings.get("target_language")
            if target:
                argv.append("--target_language")
                argv.append(str(target))

    # --- Device ----------------------------------------------------------
    device = settings.get("device")
    if device:
        argv.append("--device")
        argv.append(str(device))

    # --- Additional ------------------------------------------------------
    ignorelist = settings.get("ignorelist")
    if ignorelist:
        argv.append("--ignorelist")
        argv.append(str(ignorelist))
    if settings.get("condition_on_previous_text"):
        argv.append("--condition_on_previous_text")
    webhook = settings.get("discord_webhook")
    if webhook:
        argv.append("--discord_webhook")
        argv.append(str(webhook))
    # isolate_vocals sits before model_dir so the emitted order matches the
    # wrapper preset table (AppendAdditionalSettings puts the vocal isolation
    # branch before the model_dir append).
    if settings.get("isolate_vocals"):
        argv.append("--isolate_vocals")
        # The CLI accepts --isolate_vocals with an optional job count: a number,
        # "all", or nothing. demucs_jobs is the explicit field; a numeric or
        # "all" value in isolate_vocals itself is also carried through, since
        # that is how the settings file represents it.
        jobs = settings.get("demucs_jobs")
        if jobs is None:
            jobs = settings.get("isolate_vocals")
        if isinstance(jobs, bool):
            # The bare --isolate_vocals form; the CLI turns it into jobs "0".
            if jobs:
                argv.append("0")
        elif jobs is None or str(jobs).strip().lower() in ("", "0", "none", "false"):
            pass
        else:
            argv.append(str(jobs).strip())
    model_dir = settings.get("model_dir")
    if model_dir:
        argv.append("--model_dir")
        argv.append(str(model_dir))
    if settings.get("fp16"):
        argv.append("--fp16")
    if settings.get("auto_blocklist"):
        argv.append("--auto_blocklist")

    # --- Model source ----------------------------------------------------
    model_source = settings.get("model_source")
    if model_source:
        argv.append("--model_source")
        argv.append(str(model_source))

    return argv


def _append_web_server(argv, settings):
    """AppendWebServerSettings: port, https, serverip, always in that order."""
    portnumber = settings.get("portnumber")
    if portnumber:
        argv.append("--portnumber")
        argv.append(str(int(portnumber)))
    https_port = settings.get("https")
    if https_port:
        argv.append("--https")
        argv.append(str(int(https_port)))
    if portnumber or https_port:
        argv.append("--serverip")
        argv.append(normalize_serverip(settings.get("serverip")))


def _append_demucs(argv, settings, predicate):
    """Append --demucs_model when the caller's predicate says the mode wants it."""
    model = settings.get("demucs_model")
    if predicate and model and model != DEMUCS_DEFAULT_SENTINEL:
        argv.append("--demucs_model")
        argv.append(str(model))


def _append_captions(argv, settings):
    """AppendCapSettings."""
    if settings.get("debug"):
        argv.append("--debug")

    if settings.get("makecaptions") == "compare":
        argv.append("--makecaptions")
        argv.append("compare")
    else:
        argv.append("--makecaptions")

    file_input = settings.get("file_input")
    if file_input:
        argv.append("--file_input")
        argv.append(str(file_input))
    file_output = settings.get("file_output")
    if file_output:
        argv.append("--file_output")
        argv.append(str(file_output))
    file_output_name = settings.get("file_output_name")
    if file_output_name:
        argv.append("--file_output_name")
        argv.append(str(file_output_name))

    if settings.get("print_srt_to_console"):
        argv.append("--print_srt_to_console")
    if settings.get("silent_detect"):
        argv.append("--silent_detect")
    _flag(argv, "silent_threshold", settings.get("silent_threshold"), -35.0)
    _flag(argv, "silent_duration", settings.get("silent_duration"), 0.5)
    if settings.get("intelligent_mode"):
        argv.append("--intelligent_mode")

    # --timeout: parser_args.py:313, default 0. Emitted whenever it is set,
    # because a value the UI carries must reach the CLI. The wrapper gated it
    # behind batchjobs > 1, which silently dropped a configured timeout.
    timeout = settings.get("timeout") or 0
    if timeout > 0:
        argv.append("--timeout")
        argv.append(str(int(timeout)))

    if settings.get("word_timestamps"):
        argv.append("--word_timestamps")

    if settings.get("silent_detect"):
        _append_demucs(argv, settings, True)

    # AppendSubtitleSettings
    subtype = settings.get("subtype")
    if subtype in ("burn", "embed"):
        if subtype == "burn":
            argv.append("--subtype")
            argv.append("burn")
            substyle = settings.get("substyle")
            if substyle:
                argv.append("--substyle")
                argv.append(str(substyle))
        else:
            argv.append("--subtype")
            argv.append("embed")

    # BatchModeSettings. The wrapper calls this unconditionally in captions
    # mode, so the manual form is always emitted with its value: 1 is the CLI
    # default, which keeps the emitted command equal to the wrapper's and costs
    # nothing at runtime.
    if settings.get("adaptive_batch"):
        argv.append("--adaptive_batch")
        # The wrapper emits all three values whenever adaptive batch is on, so
        # the values the UI holds are always carried through rather than
        # relying on the CLI defaults happening to match.
        argv.append("--batchjobsize")
        argv.append(str(settings.get("batchjobsize") if settings.get("batchjobsize") is not None else 4))
        argv.append("--cpu_batches")
        argv.append(str(settings.get("cpu_batches")) if settings.get("cpu_batches") is not None
                    else "1")
        argv.append("--max_cpu_time")
        argv.append(str(settings.get("max_cpu_time") if settings.get("max_cpu_time") is not None else 300))
    else:
        batchmode = settings.get("batchmode")
        argv.append("--batchmode")
        argv.append(str(int(batchmode)) if batchmode else "1")


def _append_hls(argv, settings):
    """AppendHlsSettings. Note --stream comes after the HLS toggles."""
    cookies = settings.get("cookies")
    if cookies:
        argv.append("--cookies")
        argv.append(str(cookies))
    if settings.get("remote_hls_password_id") or settings.get("remote_hls_password"):
        _flag_always(argv, "remote_hls_password_id", settings.get("remote_hls_password_id"))
        _flag_always(argv, "remote_hls_password", settings.get("remote_hls_password"))
    if settings.get("auto_hls"):
        argv.append("--auto_hls")
    selectsource = settings.get("selectsource")
    if selectsource:
        if selectsource is True or (isinstance(selectsource, str)
                                    and selectsource.strip().lower() in ("true", "interactive")):
            # parser_args.py:285 declares nargs='?', const='interactive'. A bare
            # flag is the interactive selector; passing the literal string
            # "True" would be consumed as a format id instead.
            argv.append("--selectsource")
        else:
            argv.append("--selectsource")
            argv.append(str(selectsource))
    if settings.get("stream_original_text"):
        argv.append("--stream_original_text")

    stream = settings.get("stream")
    argv.append("--stream")
    argv.append(str(stream) if stream else "")

    stream_chunks = settings.get("stream_chunks")
    if stream_chunks is not None:
        argv.append("--stream_chunks")
        argv.append(str(int(stream_chunks)))

    paddedaudio = settings.get("paddedaudio")
    if paddedaudio:
        argv.append("--paddedaudio")
        argv.append(str(int(paddedaudio)))

    _append_demucs(argv, settings, settings.get("demucs_model") != DEMUCS_DEFAULT_SENTINEL)

    if settings.get("portnumber") or settings.get("https"):
        _append_web_server(argv, settings)


def _append_mic(argv, settings):
    """AppendMicSettings."""
    argv.append("--microphone_enabled")
    argv.append("true")
    if settings.get("energy_threshold") is not None:
        argv.append("--energy_threshold")
        argv.append(str(int(settings.get("energy_threshold"))))
    if settings.get("mic_calibration_time") is not None:
        argv.append("--mic_calibration_time")
        argv.append(str(int(settings.get("mic_calibration_time"))))
    if settings.get("record_timeout") is not None:
        argv.append("--record_timeout")
        argv.append(str(settings.get("record_timeout")))
    if settings.get("phrase_timeout") is not None:
        argv.append("--phrase_timeout")
        argv.append(str(settings.get("phrase_timeout")))
    if settings.get("set_microphone") is not None:
        argv.append("--set_microphone")
        argv.append(str(settings.get("set_microphone")))
    if settings.get("mic_chunk_size") is not None:
        argv.append("--mic_chunk_size")
        argv.append(str(int(settings.get("mic_chunk_size"))))
    paddedaudio = settings.get("paddedaudio")
    if paddedaudio:
        argv.append("--paddedaudio")
        argv.append(str(int(paddedaudio)))

    if settings.get("portnumber") or settings.get("https"):
        _append_web_server(argv, settings)


# --------------------------------------------------------------------------
# Namespace construction and validation
# --------------------------------------------------------------------------

def build_namespace(settings, argv=None):
    """Build the argparse.Namespace the CLI would end up with, as a dict.

    Values are taken from the settings the UI holds, defaults come from
    parser_args.py defaults mirrored in DEFAULTS, and the argv this module
    would build is re-applied on top so the returned object cannot disagree
    with the argv the route reports. A plain dict is returned rather than an
    argparse.Namespace because the result is serialized to JSON, and every
    value here is the same attribute main() would see.
    """
    argv = list(argv) if argv is not None else build_argv(settings)
    namespace = _namespace_defaults()
    _apply_argv(namespace, argv)
    # Mirror parser_args post-processing that the UI reads back.
    isolate = namespace.get("isolate_vocals")
    if isolate is not False and isolate is not None:
        namespace["demucs_jobs"] = isolate if isolate is not True else "0"
    else:
        namespace["demucs_jobs"] = 0
    namespace["isolate_vocals"] = bool(isolate) if isolate is not False else False
    return namespace


def _namespace_defaults():
    """Namespace values as parser_args.py would leave them."""
    values = {
        "version": None,
        "about": False,
        "checkupdate": False,
        "bugreport": False,
        "updatebranch": "master",
        "no_log": False,
        "debug": False,
        "model_source": "whisper",
        "ram": "2gb",
        "ramforce": False,
        "fp16": False,
        "compute_type": "default",
        "device": "cuda",
        "cuda_device": 0,
        "model_dir": "models",
        "intelligent_mode": False,
        "condition_on_previous_text": False,
        "language": None,
        "target_language": None,
        "translate": False,
        "transcribe": False,
        "list_microphones": False,
        "detect_sound": False,
        "set_microphone": None,
        "microphone_enabled": None,
        "energy_threshold": 100,
        "mic_calibration_time": None,
        "record_timeout": 1,
        "phrase_timeout": 1,
        "mic_chunk_size": 1,
        "paddedaudio": 0,
        "discord_webhook": None,
        "stream": None,
        "stream_original_text": False,
        "stream_chunks": 5,
        "stream_language": None,
        "stream_translate": False,
        "stream_transcribe": False,
        "auto_hls": False,
        "selectsource": None,
        "cookies": None,
        "cookies-from-browser": None,
        "remote_hls_password_id": None,
        "remote_hls_password": None,
        "makecaptions": False,
        "file_input": None,
        "file_output": None,
        "file_output_name": None,
        "word_timestamps": False,
        "subtype": None,
        "substyle": None,
        "print_srt_to_console": False,
        "silent_detect": False,
        "silent_threshold": -35.0,
        "silent_duration": 0.5,
        "batchmode": 1,
        "adaptive_batch": False,
        "cpu_batches": None,
        "max_cpu_time": 300,
        "stop_cpu_at": 0.95,
        "batchjobsize": 4,
        "isolate_vocals": False,
        "demucs_model": "htdemucs",
        "keep_temp": False,
        "timeout": 0,
        "fixsrt": None,
        "save_transcript": False,
        "save_folder": "out",
        "serverip": "127.0.0.1",
        "portnumber": None,
        "https": None,
        "launchui": False,
        "video_input": None,
        "preload": None,
        "ignorelist": None,
        "auto_blocklist": False,
    }
    return values


#: Keys whose CLI value is an int.
_ARGV_INT_KEYS = {
    "stream_chunks", "energy_threshold", "mic_calibration_time", "timeout",
    "mic_chunk_size", "paddedaudio", "batchjobsize", "cpu_batches",
    "max_cpu_time", "batchmode", "portnumber", "https", "cuda_device",
}


def _apply_argv(namespace, argv):
    """Apply a CLI argv list onto the namespace dict."""
    index = 0
    while index < len(argv):
        token = argv[index]
        if not isinstance(token, str) or not token.startswith("--"):
            index += 1
            continue
        key = token[2:]
        if key in FLAG_KEYS:
            namespace[key] = True
            index += 1
            continue
        value = None
        if index + 1 < len(argv):
            value = argv[index + 1]
        if isinstance(value, str) and value.startswith("--") and value[2:].replace("-", "_") in namespace:
            # A following flag means this one had no value.
            namespace[key] = True
            index += 1
            continue
        if key in _ARGV_INT_KEYS and value is not None:
            try:
                value = int(value)
            except (TypeError, ValueError):
                pass
        elif key in ("silent_threshold", "silent_duration", "record_timeout", "phrase_timeout", "stop_cpu_at"):
            try:
                value = float(value)
            except (TypeError, ValueError):
                pass
        namespace[key] = value
        index += 2
    return namespace


def validate_settings(settings):
    """Return an error string for a run that cannot start, else None."""
    mode = resolve_mode(settings)

    # Numeric ranges come first so a bad port or batch value is always the
    # reported reason, even when the media path is also missing.
    numeric_error = _validate_numeric_settings(settings)
    if numeric_error:
        return numeric_error

    if mode == "captions":
        if not settings.get("file_input"):
            return "captions mode needs file_input"
        if not os.path.exists(str(settings.get("file_input"))):
            return f"file_input not found: {settings.get('file_input')}"
    elif mode == "hls":
        if not settings.get("stream"):
            return "hls mode needs stream"
        stream = str(settings.get("stream"))
        if not (stream.startswith("http://") or stream.startswith("https://")):
            return "stream must be an http or https URL"
    else:
        if settings.get("set_microphone") in (None, "") and settings.get("microphone_enabled") in (None, ""):
            # The CLI will pick a default device, so this is only a warning in
            # the UI; not an error here.
            pass

    if settings.get("subtype") and mode != "captions":
        return "subtype is only valid in captions mode"
    if settings.get("subtype") and not settings.get("makecaptions"):
        return "subtype needs makecaptions"
    if settings.get("substyle") and settings.get("subtype") != "burn":
        return "substyle needs subtype burn"
    if settings.get("word_timestamps") and mode in ("hls", "mic"):
        return "word_timestamps is only supported in captions mode"

    model_source = settings.get("model_source")
    if model_source not in CHOICE_KEYS["model_source"]:
        return f"unknown model_source: {model_source}"
    device = settings.get("device")
    if device and device not in CHOICE_KEYS["device"]:
        return f"unknown device: {device}"
    demucs_model = settings.get("demucs_model")
    if demucs_model and demucs_model != DEMUCS_DEFAULT_SENTINEL and demucs_model not in CHOICE_KEYS["demucs_model"]:
        return f"unknown demucs_model: {demucs_model}"
    subtype = settings.get("subtype")
    if subtype and subtype not in CHOICE_KEYS["subtype"]:
        return f"unknown subtype: {subtype}"

    return None


def _validate_numeric_settings(settings):
    """Range-check every numeric setting against its parser_args.py validator.

    Returns an error string or None. Coercion deliberately keeps unparsable
    values (see _coerce), so this is where a typo becomes a 400 instead of
    silently turning into a default.
    """
    for key in ("portnumber", "https"):
        value = settings.get(key)
        if value in (None, "", 0):
            continue
        if isinstance(value, bool):
            return f"{key} must be an integer between 1 and 65535, got {value!r}"
        try:
            # parser_args.py:15 valid_port_number: int(value), then 1..65535.
            number = int(str(value).strip())
        except (TypeError, ValueError):
            return f"{key} must be an integer between 1 and 65535, got {value!r}"
        if number < 1 or number > 65535:
            return f"{key} must be between 1 and 65535, got {number}"

    # Numeric ranges the CLI enforces in its own validators. A value that the
    # UI sends must not reach the child process to be rejected there.
    for key in INT_KEYS:
        value = settings.get(key)
        if value is None or key in ("portnumber", "https"):
            continue
        if isinstance(value, bool):
            continue
        if key == "batchjobsize":
            continue
        try:
            int(str(value).strip())
        except (TypeError, ValueError):
            return f"{key} must be an integer, got {value!r}"
    for key in FLOAT_KEYS:
        value = settings.get(key)
        if value is None:
            continue
        try:
            float(str(value).strip())
        except (TypeError, ValueError):
            return f"{key} must be a number, got {value!r}"

    # parser_args.py:64 valid_batchmode: int, at least 1, at most the CPU count.
    batchmode = settings.get("batchmode")
    if batchmode not in (None, ""):
        try:
            batchmode_value = int(str(batchmode).strip())
        except (TypeError, ValueError):
            return f"batchmode must be an integer, got {batchmode!r}"
        max_cores = _cpu_count()
        if batchmode_value < 1:
            return f"batchmode must be at least 1, got {batchmode_value}"
        if batchmode_value > max_cores:
            return (f"batchmode ({batchmode_value}) exceeds available CPU cores "
                    f"({max_cores})")

    # parser_args.py:28 valid_batchjobsize: float between 0.1 and 12.0.
    batchjobsize = settings.get("batchjobsize")
    if batchjobsize not in (None, ""):
        try:
            batchjobsize_value = float(str(batchjobsize).strip())
        except (TypeError, ValueError):
            return f"batchjobsize must be a number between 0.1 and 12.0, got {batchjobsize!r}"
        if batchjobsize_value < 0.1 or batchjobsize_value > 12.0:
            return (f"batchjobsize must be between 0.1 and 12.0, got "
                    f"{batchjobsize_value}")

    # parser_args.py:307 --max_cpu_time is type=int with no range validator, so
    # only the integer form is checked here.
    max_cpu_time = settings.get("max_cpu_time")
    if max_cpu_time not in (None, ""):
        try:
            int(str(max_cpu_time).strip())
        except (TypeError, ValueError):
            return f"max_cpu_time must be an integer, got {max_cpu_time!r}"
    return None


def _cpu_count():
    """CPU cores, matching parser_args.get_cpu_count()."""
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1


# --------------------------------------------------------------------------
# Command construction (how the child process is launched)
# --------------------------------------------------------------------------

def _strip_ui_flags(argv):
    """Remove the UI-only flags from a run's argv.

    A run started from the UI must not open its own web server. The CLI starts
    one whenever a port is given (--portnumber/--https, or --launchui), which
    would mean a second server per run, a second PID file, and on a port
    collision a second process trying to answer the UI's own requests. The UI
    already has a server; the run only transcribes.

    Returns a new list; the caller's argv is untouched.
    """
    out = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in ("--launchui",):
            index += 1
            continue
        if token in ("--portnumber", "--https"):
            index += 2
            continue
        out.append(token)
        index += 1
    return out


def _launch_command(argv):
    """Return the executable plus argv prefix for the app, plus exec cwd.

    Frozen: the running executable re-enters itself with the CLI arguments.
    Source: the running interpreter runs synthalingua.py directly, so the run
    never depends on the shell or the venv being activated.
    """
    run_argv = _strip_ui_flags(list(argv))
    if getattr(sys, "frozen", False):
        return [sys.executable] + run_argv

    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(module_dir)
    script = os.path.join(project_root, "synthalingua.py")
    return [sys.executable, script] + run_argv


def _spawn_kwargs():
    """Platform specific flags for the child: new process group, no console."""
    kwargs = {}
    if os.name == "nt":
        flags = 0
        flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if flags:
            kwargs["creationflags"] = flags
    return kwargs


def _feed_stdin(stream, stop_event):
    """Automate the CLI's interactive prompts for a UI-driven run.

    The caption path prompts on stdin in three places and none of them can be
    skipped through argv:

    * the media segmentation menu in sub_gen.run_sub_gen ("Select option
      (1-4)"), which is offered for every file with a detectable duration and
      re-prompts forever on empty input: option 1 is "process entire file";
    * unguarded prompts such as "Press enter to exit..." and the silence
      tuning menus, where an empty answer selects the default branch;
    * the timeout recovery menu, where 1 retries with no time limit.

    So the feeder answers menus first with "1" and then keeps supplying blank
    lines, which resolves every remaining prompt to its default. A closed stdin
    (EOFError) is avoided entirely and the child can reach its own exit path
    instead of being killed. The write fails once the child is gone, which
    ends the thread.
    """
    menu_answers = 0
    while not stop_event.is_set():
        try:
            if menu_answers < MENU_ANSWER_LINES:
                stream.write("1\n")
                menu_answers += 1
            else:
                stream.write("\n")
            stream.flush()
        except (OSError, ValueError):
            return
        except Exception:
            return
        time.sleep(STDIN_FEED_INTERVAL)


def _kill_process_tree(pid):
    """Kill a process and everything it spawned on Windows.

    Returns False when the platform has no taskkill, so the caller can fall back
    to the plain terminate path.
    """
    if os.name != "nt":
        return False
    try:
        completed = subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=TASKKILL_TIMEOUT_SECONDS,
        )
    except Exception:  # noqa: BLE001
        return False
    return completed.returncode == 0


def _terminate_process(process):
    """Stop a child process and every process it spawned.

    A caption or stream run re-enters the executable for its worker, so killing
    only the direct child can leave a worker alive and still holding models or
    writing files. taskkill /T takes the whole tree, and it has to run while the
    parent is still alive for the children to be found. The plain terminate and
    kill calls stay as the fallback for other platforms and for the case where
    taskkill is unavailable.
    """
    if process is None or process.poll() is not None:
        return
    if _kill_process_tree(process.pid):
        try:
            process.wait(timeout=STOP_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            pass
        return
    try:
        process.terminate()
    except OSError:
        pass
    try:
        process.wait(timeout=STOP_GRACE_SECONDS)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=STOP_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass


# --------------------------------------------------------------------------
# Model and device discovery (read only)
# --------------------------------------------------------------------------

def models_dir(model_dir=None):
    """Resolve the models folder the same way synthalingua.py main() does."""
    if model_dir:
        return os.path.abspath(str(model_dir))
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "models")
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(module_dir)
    return os.path.join(project_root, "models")


def _safe_listdir(path):
    try:
        return sorted(os.listdir(path))
    except OSError:
        return []


def list_available_models(model_dir=None):
    """List the model families present on disk. Read only, never writes.

    The models folder is the single real copy of about 32 GiB of weights. This
    function only lists directory names; it never creates, moves or deletes
    anything.
    """
    root = models_dir(model_dir)
    result = {
        "model_dir": root,
        "whisper": [],
        "fasterwhisper": [],
        "openvino": [],
        "demucs": [],
    }

    whisper_root = os.path.join(root, "Whisper")
    result["whisper"] = [
        name for name in _safe_listdir(whisper_root)
        if name.lower().endswith(".pt")
    ]

    faster_root = os.path.join(root, "FasterWhisper")
    faster = []
    for name in _safe_listdir(faster_root):
        if name.startswith("models--"):
            faster.append(name.replace("models--", "", 1).replace("--", "/", 1) if name.count("--") >= 2 else name)
    result["fasterwhisper"] = faster

    openvino_root = os.path.join(root, "OpenVINO")
    openvino = []
    for publisher in _safe_listdir(openvino_root):
        publisher_path = os.path.join(openvino_root, publisher)
        if not os.path.isdir(publisher_path):
            continue
        for name in _safe_listdir(publisher_path):
            if os.path.isdir(os.path.join(publisher_path, name)):
                openvino.append(name)
    result["openvino"] = openvino

    demucs_root = os.path.join(root, "demucs")
    result["demucs"] = [
        name for name in _safe_listdir(demucs_root)
        if name.lower().endswith(".th")
    ]

    return result


def list_microphones():
    """List input devices using sounddevice when it is importable."""
    devices = []
    default_index = None
    try:
        import sounddevice as sd

        raw = sd.query_devices()
        default_input = None
        try:
            default_input = sd.default.device[0]
        except (TypeError, IndexError, AttributeError):
            default_input = None
        for index, device in enumerate(raw):
            try:
                channels = int(device.get("max_input_channels", 0))
            except Exception:
                channels = 0
            if channels <= 0:
                continue
            devices.append({
                "index": index,
                "name": str(device.get("name", f"device {index}")),
                "channels": channels,
                "default_samplerate": device.get("default_samplerate"),
            })
        if default_input is not None:
            default_index = int(default_input)
            if not any(entry["index"] == default_index for entry in devices):
                default_index = None
    except Exception:
        # No audio stack (or no sounddevice) is not an error for the UI: an
        # empty list means "type the device name".
        return {"devices": [], "default_index": None}
    return {"devices": devices, "default_index": default_index}


def read_blocklist(path=None):
    """Read the word blocklist. Returns words plus the path when found."""
    candidates = []
    if path:
        candidates.append(str(path))
    else:
        candidates.append("ignorelist.txt")
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(module_dir)
        candidates.append(os.path.join(project_root, "ignorelist.txt"))
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(os.path.join(appdata, APP_DIR_NAME, "ignorelist.txt"))

    for candidate in candidates:
        try:
            if not os.path.isfile(candidate):
                continue
            with open(candidate, "r", encoding="utf-8") as handle:
                words = [line.strip() for line in handle if line.strip()]
            return {"words": words, "path": os.path.abspath(candidate)}
        except OSError:
            continue
    return {"words": [], "path": None}


def list_languages():
    """Languages the CLI already accepts, from modules.languages.

    parser_args accepts both codes and display names, so this returns the code
    and display name pairs the app can derive plus the flat list of every value
    the CLI really accepts. No list is invented here.
    """
    try:
        from modules.languages import get_valid_languages
        values = list(get_valid_languages())
    except Exception:
        values = []

    codes = [value for value in values if len(value) <= 3 and value.isalpha() and value.islower()]
    names = [value for value in values if value not in codes]
    pairs = []
    if len(names) == len(codes):
        pairs = [{"code": code, "name": name} for code, name in zip(codes, names)]
    else:
        pairs = [{"code": None, "name": value} for value in values]
    return {"languages": pairs, "values": values}


# --------------------------------------------------------------------------
# Run manager
# --------------------------------------------------------------------------

class RunManager:
    """Owns the single run slot: state, child process, log ring buffer."""

    def __init__(self):
        self._lock = threading.RLock()
        self._process = None
        self._stdin_thread = None
        self._stdin_stop = threading.Event()
        self._readers = []
        self._state = "idle"
        self._mode = None
        self._run_id = None
        self._started_at = None
        self._finished_at = None
        self._started_monotonic = None
        self._finished_monotonic = None
        self._exit_code = None
        self._error = None
        self._stop_requested = False
        self._lines = []
        self._next_line_number = 0
        self._socketio = None

    # -- wiring -----------------------------------------------------------

    def set_socketio(self, socketio):
        """Attach the SocketIO instance used for run_log / run_state events."""
        with self._lock:
            self._socketio = socketio

    def _emit(self, event, payload):
        socketio = self._socketio
        if socketio is None:
            return
        try:
            socketio.emit(event, payload)
        except Exception:
            # A dead browser must never break a run.
            pass

    # -- state ------------------------------------------------------------

    def snapshot(self, include_tail=True):
        """The /api/run/status payload, exactly as CONTRACT v1 documents it."""
        with self._lock:
            running = self._state in ("starting", "running", "stopping")
            elapsed = None
            if self._started_monotonic is not None:
                end = self._finished_monotonic if self._finished_monotonic is not None else time.monotonic()
                elapsed = round(end - self._started_monotonic, 3)
            payload = {
                "state": self._state,
                "mode": self._mode,
                "running": running,
                "started_at": self._started_at,
                "elapsed_s": elapsed,
                "exit_code": self._exit_code,
                "error": self._error,
                "log_lines": len(self._lines),
            }
            if include_tail:
                payload["log_tail"] = list(self._lines[-LOG_TAIL_MAX:])
            else:
                payload["log_tail"] = []
            return payload

    def _state_event(self):
        with self._lock:
            return {
                "state": self._state,
                "mode": self._mode,
                "started_at": self._started_at,
                "elapsed_s": self.snapshot(include_tail=False)["elapsed_s"],
                "exit_code": self._exit_code,
                "error": self._error,
            }

    def _set_state(self, state, error=None, exit_code=None):
        with self._lock:
            self._state = state
            if error is not None or state != "error":
                self._error = error
            if exit_code is not None:
                self._exit_code = exit_code
            if state in ("stopped", "error"):
                if self._finished_monotonic is None:
                    self._finished_monotonic = time.monotonic()
                    self._finished_at = _iso_now()
        self._emit(EVENT_RUN_STATE, self._state_event())

    def is_active(self):
        with self._lock:
            return self._state in ("starting", "running", "stopping")

    def run_id(self):
        """Identifier of the current or last run, or None before the first."""
        with self._lock:
            return self._run_id

    # -- log --------------------------------------------------------------

    def _append_line(self, line):
        with self._lock:
            number = self._next_line_number
            self._next_line_number += 1
            self._lines.append(line)
            if len(self._lines) > LOG_BUFFER_MAX:
                del self._lines[: len(self._lines) - LOG_BUFFER_MAX]
        self._emit(EVENT_RUN_LOG, {"line": line, "n": number})

    def log_since(self, since=0, limit=None):
        """Lines after index `since` plus the next index to ask for."""
        try:
            since = int(since)
        except (TypeError, ValueError):
            since = 0
        with self._lock:
            start = max(0, min(since, self._next_line_number))
            first_buffered = self._next_line_number - len(self._lines)
            offset = max(0, start - first_buffered)
            lines = list(self._lines[offset:])
            next_index = self._next_line_number
        if limit is not None and limit >= 0:
            lines = lines[:limit]
            if lines:
                next_index = since + len(lines)
        return {"lines": lines, "next": next_index}

    # -- start / stop -----------------------------------------------------

    def start(self, settings, argv=None):
        """Start a run. Returns (snapshot, error). Only one run at a time."""
        with self._lock:
            if self.is_active():
                return None, "a run is already active"

            argv = list(argv) if argv is not None else build_argv(settings)
            mode = resolve_mode(settings)
            command = _launch_command(argv)
            cwd = _run_cwd(settings)

            self._state = "starting"
            self._mode = mode
            self._run_id = uuid.uuid4().hex
            self._started_at = _iso_now()
            self._started_monotonic = time.monotonic()
            self._finished_at = None
            self._finished_monotonic = None
            self._exit_code = None
            self._error = None
            self._stop_requested = False
            self._lines = []
            self._next_line_number = 0

        self._emit(EVENT_RUN_STATE, self._state_event())
        self._append_line(f"$ {arg_line(argv)}")

        env = _child_env()
        kwargs = _spawn_kwargs()
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                **kwargs,
            )
        except (OSError, ValueError) as exc:
            with self._lock:
                self._process = None
            self._set_state("error", error=f"could not start the run: {exc}", exit_code=None)
            return self.snapshot(), None

        with self._lock:
            self._process = process
            self._state = "running"

        self._emit(EVENT_RUN_STATE, self._state_event())

        self._stdin_stop.clear()
        if process.stdin is not None:
            self._stdin_thread = threading.Thread(
                target=_feed_stdin,
                args=(process.stdin, self._stdin_stop),
                name="run-manager-stdin",
                daemon=True,
            )
            self._stdin_thread.start()

        stdout_thread = threading.Thread(
            target=self._read_stream,
            args=(process.stdout,),
            name="run-manager-stdout",
            daemon=True,
        )
        stdout_thread.start()
        waiter = threading.Thread(
            target=self._wait_for_exit,
            args=(process,),
            name="run-manager-waiter",
            daemon=True,
        )
        waiter.start()
        with self._lock:
            self._readers = [stdout_thread, waiter]
        return self.snapshot(), None

    def stop(self):
        """Stop the active run. Returns the status snapshot."""
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None:
                if self._state not in ("idle",):
                    self._exit_code = process.returncode if process is not None else self._exit_code
                    self._finished_monotonic = self._finished_monotonic or time.monotonic()
                    self._state = "stopped" if self._state != "error" else "error"
                    self._finished_at = self._finished_at or _iso_now()
                else:
                    self._state = "idle"
            else:
                self._stop_requested = True
                self._state = "stopping"

        if process is None or process.poll() is not None:
            self._emit(EVENT_RUN_STATE, self._state_event())
            return self.snapshot()

        self._emit(EVENT_RUN_STATE, self._state_event())
        self._append_line("stop requested")
        _terminate_process(process)
        return self.snapshot()

    def wait(self, timeout=None):
        """Wait for the run to finish (used by tests and shutdown)."""
        with self._lock:
            process = self._process
        if process is None:
            return self.snapshot()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return self.snapshot()
        deadline = time.monotonic() + (timeout or 0) + 1.0
        while time.monotonic() < deadline:
            with self._lock:
                if self._state not in ("starting", "running", "stopping"):
                    break
            time.sleep(0.05)
        return self.snapshot()

    def shutdown(self):
        """Stop any run and stop the feeder thread. Called at server shutdown."""
        try:
            with self._lock:
                process = self._process
            if process is not None and process.poll() is None:
                self.stop()
        finally:
            self._stdin_stop.set()
            with self._lock:
                stream = self._process.stdin if self._process is not None else None
            if stream is not None:
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass

    # -- internals --------------------------------------------------------

    def _read_stream(self, stream):
        if stream is None:
            return
        try:
            for raw in iter(stream.readline, ""):
                self._append_line(raw.rstrip("\r\n"))
        except (OSError, ValueError):
            pass
        finally:
            try:
                stream.close()
            except (OSError, ValueError):
                pass

    def _wait_for_exit(self, process):
        try:
            code = process.wait()
        except Exception:
            code = None
        self._stdin_stop.set()

        with self._lock:
            stopped_by_user = self._stop_requested
            self._exit_code = code
            self._process = None
            if stopped_by_user:
                self._state = "stopped"
            elif code == 0:
                self._state = "stopped"
            else:
                self._state = "error"
                if self._error is None:
                    self._error = f"run exited with code {code}"
            self._finished_monotonic = time.monotonic()
            self._finished_at = _iso_now()

        self._append_line(f"run finished with exit code {code}")
        self._emit(EVENT_RUN_STATE, self._state_event())


def _iso_now():
    """Local ISO 8601 timestamp for the UI."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _run_cwd(settings):
    """Working directory for the child process: one owned folder per run.

    A captions run ends by deleting "server.pid" in its working directory, and
    the UI server uses that same file for its own watchdog. If the child shared
    the server's working directory, finishing one caption job would delete the
    running server's PID file and the watchdog would shut the UI down mid-use.

    Each run therefore gets <server cwd>/temp/run_children/<run_id>/, so both
    processes keep their own PID file and neither can stop the other. Relative
    paths the app resolves against the working directory, such as the sub_gen
    session folder and "./" outputs, stay under the app folder as before. The
    run's own folder is left for the app's temp cleanup, the same as every other
    temp file the app creates.
    """
    base = _base_cwd()
    run_dir = os.path.join(base, "temp", "run_children", uuid.uuid4().hex)
    try:
        os.makedirs(run_dir, exist_ok=True)
    except OSError:
        return base
    return run_dir


def _base_cwd():
    """The working directory the app itself runs from."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    module_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(module_dir)


def _child_env():
    """Environment for the child: same as ours, plus unbuffered UTF-8 output."""
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


#: The single run slot for the process. Created on first use so importing this
#: module starts nothing.
_MANAGER = None


def get_manager():
    """Return the process-wide RunManager, creating it on first use."""
    global _MANAGER
    with _RUN_LOCK:
        if _MANAGER is None:
            _MANAGER = RunManager()
        return _MANAGER


def get_settings():
    """Convenience: current persisted settings."""
    return load_settings()


def preview(settings_patch=None):
    """Merge a patch, then return argv, namespace and mode."""
    settings = load_settings()
    if settings_patch:
        settings = merge_settings(settings, settings_patch)
    argv = build_argv(settings)
    namespace = build_namespace(settings, argv)
    return {
        "argv": argv,
        "namespace": namespace,
        "mode": resolve_mode(settings),
        "settings": settings,
        "command_line": arg_line(argv),
    }
