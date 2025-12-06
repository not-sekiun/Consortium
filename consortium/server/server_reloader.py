import os
import subprocess
import sys
import time
from datetime import datetime

from prompt_toolkit import HTML, print_formatted_text
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from consortium.server.server_config import (
    CONSORTIUM_AGENTS_DIRECTORY_PATH,
    CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH,
    CONSORTIUM_LISTENER_PROFILES_DIRECTORY_PATH,
    CONSORTIUM_PLUGINS_DIRECTORY_PATH,
)


class _ServerSubprocessManager:
    def __init__(self, server_subprocess_arguments: list[str]):
        self._server_subprocess_arguments = server_subprocess_arguments
        self._process = None
        self.start_server()

    def start_server(self) -> None:
        self._process = subprocess.Popen(self._server_subprocess_arguments)

    def stop_server(self) -> None:
        self._process.terminate()
        self._process.wait()

    def restart_server(self) -> None:
        self.stop_server()
        self.start_server()


class _ServerReloaderEventHandler(FileSystemEventHandler):
    def __init__(self, server_subprocess_manager: _ServerSubprocessManager):
        self._server_subprocess_manager = server_subprocess_manager
        self._last_reloaded = time.time()
        # Many file events can be triggered in rapid succession for a file change. We
        # only want to reload the server if the file changes occurred at least
        # `self._minumum_seconds_between_reloads` seconds apart to prevent rapid
        # reloading.
        self._minimum_seconds_between_reloads = 5.0

    def on_any_event(self, event: FileSystemEvent) -> None:
        if time.time() - self._last_reloaded < self._minimum_seconds_between_reloads:
            return

        _print_delimiter_text(
            f"[{datetime.now().isoformat()}] Detected file change. Reloading server...",
        )
        self._server_subprocess_manager.restart_server()
        self._last_reloaded = time.time()


def _print_delimiter_text(text) -> None:
    terminal_width = os.get_terminal_size()[0]
    if terminal_width < len(text) + 2:
        output = text
    else:
        text = f" {text} "
        padding = (terminal_width - len(text)) // 2
        output = "=" * padding + text + "=" * padding
    print_formatted_text(HTML(f"<b><ansigreen>{output}</ansigreen></b>"))


def main() -> None:
    _print_delimiter_text(
        f"[{datetime.now().isoformat()}] Starting server with framework reloading "
        f"enabled...",
    )
    filtered_arguments = [
        argument for argument in sys.argv if argument not in ["-r", "--reload"]
    ]
    server_subprocess_arguments = sys.executable.split(" ") + filtered_arguments
    server_subprocess_manager = _ServerSubprocessManager(server_subprocess_arguments)
    event_handler = _ServerReloaderEventHandler(
        server_subprocess_manager=server_subprocess_manager,
    )

    observed_directories = [
        str(CONSORTIUM_LISTENER_PROFILES_DIRECTORY_PATH.resolve()),
        str(CONSORTIUM_AGENTS_DIRECTORY_PATH.resolve()),
        str(CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH.resolve()),
        str(CONSORTIUM_PLUGINS_DIRECTORY_PATH.resolve()),
    ]
    observer = Observer()
    for directory in observed_directories:
        observer.schedule(event_handler, directory, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        server_subprocess_manager.stop_server()
        _print_delimiter_text(
            f"[{datetime.now().isoformat()}] Stopping server...",
        )
