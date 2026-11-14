"""pywebview desktop shell for Synthalingua.

Hosts the existing Flask web UI in a native window, so the app can ship
without the .NET wrapper. The shell is deliberately thin:

* it starts the app's own server through ``modules.api_backend.start_desktop_server``
* it opens the main window on ``/main.html`` (falling back to ``/index.html``)
* it marks every page with ``window.__synthalinguaShell = true`` and forwards
  OS file drops to ``window.__synthalinguaDrop(paths)`` with absolute paths
* it exposes the CONTRACT v1 js_api (caption window, file picker, env, quit)

Importing this module has no side effects: pywebview is imported inside
``main()`` so a missing dependency produces a clear message, not a traceback
at import time. The Windows app entry point only ever calls ``main()``.

Window transparency is intentionally not used here. The spike found the
EdgeChromium backend accepts ``transparent=True`` but the result was not
visually confirmed, so the caption window uses a plain frameless, always on
top window, which the spike did prove.
"""
from __future__ import annotations

import ctypes
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_HOST = "127.0.0.1"
PORT_HINT = 8000
MAIN_WINDOW_SIZE = (1280, 840)
CAPTION_WINDOW_SIZE = (900, 220)
CAPTION_WINDOW_TITLE = "Synthalingua Captions"
SINGLE_INSTANCE_MUTEX = "Local\\SynthalinguaDesktopShell"

# Shutdown budgets. The run grace has to clear the run manager's own stop grace,
# which is the time the child tree gets before the manager kills it.
SHUTDOWN_RUN_GRACE_SECONDS = 8.0
# Deleting server.pid is a requested shutdown, so it must not look like a crash.
FORCED_SHUTDOWN_EXIT_CODE = 0

# SetWindowPos / GetWindowLong constants used to toggle always-on-top.
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008

log = logging.getLogger("synthalingua.desktop")

# Holds the single-instance mutex handle for the process lifetime. Releasing it
# would let a second instance start while this one is still running.
_mutex_handle = None


def _load_webview():
    """Import pywebview lazily. Returns (webview, DOMEventHandler) or None."""
    try:
        import webview
        from webview.dom import DOMEventHandler
    except Exception as exc:  # noqa: BLE001 - any import failure is reported
        missing = getattr(exc, "name", None) or "pywebview"
        print("The desktop UI needs pywebview (%s could not be imported)." % missing)
        print("Install it with: pip install pywebview")
        print("Details: %s" % exc)
        return None
    return webview, DOMEventHandler


def _acquire_single_instance():
    """True when this process may run the shell.

    Windows named mutex, released automatically when the process exits, so a
    crash never leaves a stale lock. Any failure of the guard itself is treated
    as 'no guard' so the UI still starts.
    """
    global _mutex_handle
    if os.name != "nt":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX)
        already_exists = 183  # ERROR_ALREADY_EXISTS
        if kernel32.GetLastError() == already_exists:
            if handle:
                kernel32.CloseHandle(handle)
            return False
        _mutex_handle = handle
        return True
    except Exception:  # noqa: BLE001 - never block startup on the guard
        return True


def _app_version():
    try:
        import importlib.metadata as metadata

        return metadata.version("synthalingua")
    except Exception:  # noqa: BLE001
        return "unknown"


def _something_listening(host, port, timeout=0.3):
    """True when something already accepts connections on host:port."""
    import socket

    if port in (None, 0):
        return False
    try:
        with socket.create_connection((host, int(port)), timeout):
            return True
    except OSError:
        return False


def _caption_hwnd(title=CAPTION_WINDOW_TITLE):
    """Native handle of the caption window, looked up by its unique title."""
    if os.name != "nt":
        return 0
    try:
        return int(ctypes.windll.user32.FindWindowW(None, title) or 0)
    except Exception:  # noqa: BLE001
        return 0


def _caption_topmost(hwnd):
    """True when the window currently carries WS_EX_TOPMOST."""
    try:
        style = ctypes.windll.user32.GetWindowLongW(ctypes.c_void_p(hwnd), GWL_EXSTYLE)
        return bool(style & WS_EX_TOPMOST)
    except Exception:  # noqa: BLE001
        return False


def _set_caption_topmost(hwnd, topmost):
    """Toggle always-on-top with SetWindowPos.

    The toolkit's own on_top setter marshals through pythonnet, and in the
    frozen build that deadlocked the whole process: the property write runs on
    the WebView2 message thread while its Invoke waits for the GUI thread, which
    is itself waiting for that same js_api call to return. SetWindowPos acts on
    a handle, so neither thread can be blocked.
    """
    try:
        return bool(ctypes.windll.user32.SetWindowPos(
            ctypes.c_void_p(hwnd),
            ctypes.c_void_p(HWND_TOPMOST if topmost else HWND_NOTOPMOST),
            0, 0, 0, 0,
            SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE,
        ))
    except Exception:  # noqa: BLE001
        return False


def _page_served(url):
    """True when the URL answers with a successful HTTP status."""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return 200 <= response.status < 400
    except urllib.error.HTTPError as exc:
        return 200 <= exc.code < 400
    except Exception:  # noqa: BLE001
        return False


class ShellApi:
    """js_api exposed to every page as pywebview.api."""

    def __init__(self, shell):
        self._shell = shell

    def open_caption_window(self):
        return self._shell.open_caption_window()

    def close_caption_window(self):
        return self._shell.close_caption_window()

    def set_caption_pinned(self, pinned=True):
        return self._shell.set_caption_pinned(pinned)

    def pick_file(self, kind="audio_video"):
        return self._shell.pick_file(kind)

    def get_env(self):
        return self._shell.get_env()

    def quit_app(self):
        return self._shell.quit_app()


class DesktopShell:
    def __init__(self, webview, dom_event_handler, host=DEFAULT_HOST, port=None):
        self._webview = webview
        self._DOMEventHandler = dom_event_handler
        self._host = host
        self._port = port
        self._url = None
        self._main = None
        self._caption = None
        self._caption_pinned = True
        self._caption_rect = None
        self._quit = False
        self._forced_shutdown = False
        self._drop_bound = set()
        self.api = ShellApi(self)

    # -- window construction -------------------------------------------------

    def _create_main_window(self, page_url):
        width, height = MAIN_WINDOW_SIZE
        window = self._webview.create_window(
            "Synthalingua",
            page_url,
            width=width,
            height=height,
            min_size=(900, 600),
            js_api=self.api,
        )
        window.events.loaded += lambda: self._on_page_loaded(window)
        window.events.closed += self._on_main_closed
        return window

    def _create_caption_window(self, geometry=None, pinned=True):
        x, y, width, height = self._caption_bounds(geometry)
        window = self._webview.create_window(
            CAPTION_WINDOW_TITLE,
            "%s/caption_window.html" % self._url,
            width=width,
            height=height,
            x=x,
            y=y,
            frameless=True,
            on_top=pinned,
            easy_drag=True,
            js_api=self.api,
        )
        window.events.loaded += lambda: self._on_page_loaded(window)
        # Geometry is tracked from window events instead of being read back from
        # the native window: the position and size properties wait on the GUI
        # thread, which is not safe to do from a js_api call.
        self._caption_rect = (x, y, width, height)
        try:
            window.events.resized += self._on_caption_resized
            window.events.moved += self._on_caption_moved
        except Exception as exc:  # noqa: BLE001
            log.warning("could not track the caption window geometry: %s", exc)
        return window

    def _caption_bounds(self, geometry=None):
        """(x, y, width, height), from an explicit geometry or the last known one."""
        rect = geometry or self._caption_rect
        if not rect:
            return (None, None, CAPTION_WINDOW_SIZE[0], CAPTION_WINDOW_SIZE[1])
        x, y, width, height = rect
        return (x, y, width, height)

    def _on_caption_resized(self, width, height):
        x, y, _, _ = self._caption_bounds()
        self._caption_rect = (x, y, width, height)

    def _on_caption_moved(self, x, y):
        _, _, width, height = self._caption_bounds()
        self._caption_rect = (x, y, width, height)

    def _caption_preferences(self):
        """(pinned, geometry) persisted by the caption page and the main panel.

        ui_caption_pinned drives frameless and always-on-top; ui_caption_geometry
        is the {x, y, width, height} object the caption page records on resize.
        Anything unreadable falls back to defaults rather than blocking the open.
        """
        try:
            from modules import run_manager

            settings = run_manager.load_settings() or {}
        except Exception as exc:  # noqa: BLE001
            settings = {}
            log.warning("could not read the caption window settings: %s", exc)
        pinned = bool(settings.get("ui_caption_pinned", True))
        geometry = None
        raw = settings.get("ui_caption_geometry")
        if isinstance(raw, dict):
            try:
                width = int(raw.get("width") or 0)
                height = int(raw.get("height") or 0)
                x = raw.get("x")
                y = raw.get("y")
                x = int(x) if isinstance(x, (int, float)) else None
                y = int(y) if isinstance(y, (int, float)) else None
            except Exception:  # noqa: BLE001
                width = height = 0
            if width > 0 and height > 0:
                geometry = (x, y, width, height)
        return pinned, geometry

    # -- page wiring ---------------------------------------------------------

    def _on_page_loaded(self, window):
        self._mark_shell(window)
        self._bind_drop(window)

    def _mark_shell(self, window):
        """Tell the page it is hosted by the shell.

        The flag is set after the page has loaded, which is later than the page's
        own boot and later than its pywebviewready handler, so on its own the
        page's shell-only controls would stay hidden. Setting the flag is
        therefore followed by a fresh pywebviewready event: that event is the
        page's documented shell signal, and its handlers only re-apply
        visibility (main.js refreshShellUi, caption_window.html
        updateShellControls), so re-running them is idempotent and does no work
        beyond class and title updates.

        Pages can also define window.__synthalinguaShellReady and have it called
        here instead of listening for the event.
        """
        script = (
            "window.__synthalinguaShell = true;"
            "if (typeof window.__synthalinguaShellReady === 'function')"
            " { try { window.__synthalinguaShellReady(); } catch (e) {} }"
            "try { window.dispatchEvent(new Event('pywebviewready')); } catch (e) {}"
        )
        try:
            window.evaluate_js(script)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not mark page as shell-hosted: %s", exc)

    def _bind_drop(self, window):
        if window.uid in self._drop_bound:
            return
        try:
            window.dom.document.events.drop += self._DOMEventHandler(
                lambda event: self._handle_drop(window, event)
            )
            self._drop_bound.add(window.uid)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not bind the window drop handler: %s", exc)

    def _handle_drop(self, window, event):
        paths = self._extract_paths(event)
        if not paths:
            return
        log.info("dropped %d file(s): %s", len(paths), ", ".join(paths))
        script = "window.__synthalinguaDrop && window.__synthalinguaDrop(%s)" % json.dumps(paths)
        try:
            window.evaluate_js(script)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not deliver the drop to the page: %s", exc)

    @staticmethod
    def _extract_paths(event):
        """Absolute paths from a pywebview drop event (pywebviewFullPath)."""
        paths = []
        if not isinstance(event, dict):
            return paths
        for item in (event.get("dataTransfer", {}) or {}).get("files", []) or []:
            full_path = item.get("pywebviewFullPath") if isinstance(item, dict) else None
            if full_path:
                paths.append(full_path)
        return paths

    # -- js_api --------------------------------------------------------------

    def open_caption_window(self):
        if self._caption is not None:
            try:
                self._caption.on_top = self._caption_pinned
                self._caption.restore()
                self._caption.show()
            except Exception as exc:  # noqa: BLE001
                log.warning("could not raise the caption window: %s", exc)
            return {"ok": True, "created": False}
        if not _page_served("%s/caption_window.html" % self._url):
            message = "caption_window.html is not served yet"
            log.warning(message)
            return {"ok": False, "error": message}
        pinned, geometry = self._caption_preferences()
        self._caption_pinned = pinned
        self._caption = self._create_caption_window(geometry, pinned)
        return {"ok": True, "created": True, "pinned": pinned,
                "geometry": list(self._caption_rect)}

    def close_caption_window(self):
        if self._caption is None:
            return {"ok": True, "closed": False}
        try:
            self._caption.destroy()
        except Exception as exc:  # noqa: BLE001
            log.warning("could not close the caption window: %s", exc)
        self._caption = None
        return {"ok": True, "closed": True}

    def set_caption_pinned(self, pinned=True):
        """Pin state is always-on-top only. The window is never rebuilt.

        frameless is applied when a native window is created, so toggling it
        used to mean destroying and recreating the caption window. That teardown
        ran inside the js_api call made by the window's own page and hung the
        app (reproduced in source and in the frozen build), and the recreated
        page lost its planted layout. The caption window is therefore created
        frameless once and pinning only toggles the native always-on-top flag
        plus the page's own planted styling.
        """
        pinned = bool(pinned)
        self._caption_pinned = pinned
        if self._caption is None:
            return {"ok": False, "error": "caption window is not open", "pinned": pinned}
        hwnd = _caption_hwnd()
        if not hwnd:
            log.warning("caption window handle not found; always-on-top left unchanged")
            return {"ok": False, "error": "caption window handle not found", "pinned": pinned}
        if not _set_caption_topmost(hwnd, pinned):
            return {"ok": False, "error": "SetWindowPos failed", "pinned": pinned}
        return {"ok": True, "pinned": pinned, "topmost": _caption_topmost(hwnd),
                "recreated": False}

    def pick_file(self, kind="audio_video"):
        kinds = {
            "audio_video": (
                ("Audio and video (*.mp4;*.mkv;*.mov;*.avi;*.webm;*.mp3;*.wav;*.m4a;*.flac;*.ogg;*.aac)",),
                "open",
            ),
            "cookies": (("Cookies (*.txt;*.json)", "All files (*.*)"), "open"),
            "ignorelist": (("Text (*.txt)", "All files (*.*)"), "open"),
            "srt": (("Subtitles (*.srt)", "All files (*.*)"), "open"),
            "output_dir": (None, "folder"),
        }
        file_types, mode = kinds.get(kind, kinds["audio_video"])
        if mode == "folder":
            dialog_type = self._dialog_type("FOLDER", 20)
        else:
            dialog_type = self._dialog_type("OPEN", 10)
        try:
            result = self._main.create_file_dialog(
                dialog_type, allow_multiple=False, file_types=file_types or ()
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("file dialog failed: %s", exc)
            return {"path": None, "error": str(exc)}
        if not result:
            return {"path": None}
        if isinstance(result, (list, tuple)):
            return {"path": result[0] if result else None}
        return {"path": result}

    def _dialog_type(self, name, fallback):
        file_dialog = getattr(self._webview, "FileDialog", None)
        return getattr(file_dialog, name, fallback) if file_dialog else fallback

    def get_env(self):
        return {
            "shell": True,
            "frozen": bool(getattr(sys, "frozen", False)),
            "version": _app_version(),
        }

    def quit_app(self):
        self._quit = True
        self._stop_active_run()
        for window in list(getattr(self._webview, "windows", []) or []):
            try:
                window.destroy()
            except Exception:  # noqa: BLE001
                pass
        return {"ok": True, "quitting": True}

    def _on_main_closed(self):
        self._quit = True
        self._stop_active_run()
        self.close_caption_window()

    def _stop_active_run(self):
        """Stop the manager's run so no child process outlives the shell.

        The run child re-enters the executable for its worker, and the manager's
        stop path is what takes that tree down, so quitting without this leaves
        the run and its worker behind.
        """
        try:
            from modules import run_manager

            manager = run_manager.get_manager()
        except Exception as exc:  # noqa: BLE001
            log.warning("could not reach the run manager: %s", exc)
            return
        try:
            manager.stop()
            manager.wait(timeout=SHUTDOWN_RUN_GRACE_SECONDS)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not stop the active run: %s", exc)

    def _on_forced_shutdown(self):
        """server.pid was deleted: stop the run, stop the server, exit 0.

        Registered with api_backend, which calls this from its watchdog. The exit
        is deliberate rather than graceful. Measured on this build, the GUI unwinding
        after the windows are destroyed keeps the GIL for around 12 seconds, and a
        Python-level deadline thread sleeps through it, so the kill switch has to
        land here while this thread is the one holding the GIL. Everything that
        matters is done first: the run is stopped through the manager, which takes
        the child tree down with taskkill, and the server is stopped with a short
        join instead of the 5 second one the normal exit path allows.

        The exit code stays 0 so a requested shutdown through the pid file does not
        look like a crash.
        """
        if self._forced_shutdown:
            return
        self._forced_shutdown = True
        self._quit = True
        log.info("server.pid was removed; closing the desktop shell and its runs")
        self._stop_active_run()
        try:
            from modules.api_backend import stop_desktop_server

            stop_desktop_server(timeout=0.5)
        except Exception:  # noqa: BLE001
            pass
        log.info("desktop shell exiting because server.pid was removed")
        os._exit(FORCED_SHUTDOWN_EXIT_CODE)

    # -- lifecycle -----------------------------------------------------------

    def run(self):
        from modules.api_backend import (  # lazy: importing this module must not boot anything
            find_available_port,
            register_shutdown_callback,
            start_desktop_server,
            stop_desktop_server,
            unregister_shutdown_callback,
        )

        candidate = self._port
        if candidate in (None, 0):
            candidate = find_available_port(PORT_HINT, self._host)
            if candidate is None:
                log.warning("no available port found in the preferred range, letting the OS pick one")
                candidate = 0
            # find_available_port sets SO_REUSEADDR, which on Windows can report a
            # port another process is already serving. Never attach the shell to a
            # server this process does not own: fall back to an OS-assigned port.
            elif _something_listening(self._host, candidate):
                log.warning("port %s is already in use, letting the OS pick a port", candidate)
                candidate = 0
        try:
            url, bound_port, thread = start_desktop_server(host=self._host, port=candidate)
        except Exception as exc:  # noqa: BLE001
            log.error("could not start the desktop server: %s", exc)
            return 2
        self._url = url
        log.info("serving the desktop UI at %s (port %s)", url, bound_port)

        page = "/main.html"
        if not _page_served(url + page):
            log.warning("main.html is not served yet, falling back to index.html")
            page = "/index.html"
        self._main = self._create_main_window(url + page)

        # Deleting server.pid is a kill switch: the watchdog sets its flag, and
        # this is what turns that flag into the shell actually going away.
        register_shutdown_callback(self._on_forced_shutdown)
        try:
            self._webview.start(self._on_gui_started)
        finally:
            unregister_shutdown_callback(self._on_forced_shutdown)
            stop_desktop_server()
        return 0

    def _on_gui_started(self):
        log.info("desktop UI ready at %s", self._url)
        while not self._quit and self._webview.windows:
            time.sleep(0.3)


def main(host=DEFAULT_HOST, port=None):
    """Run the desktop shell. Returns the process exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not _acquire_single_instance():
        print("Synthalingua desktop UI is already running.")
        return 1
    loaded = _load_webview()
    if loaded is None:
        return 2
    webview, dom_event_handler = loaded
    shell = DesktopShell(webview, dom_event_handler, host=host, port=port)
    return shell.run()


if __name__ == "__main__":
    raise SystemExit(main())
