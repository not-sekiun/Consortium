import os
import sys


def _terminal_supports_title() -> bool:
    """Best-effort check for whether stdout is a terminal that will
    sensibly interpret an OSC 'set title' escape sequence."""

    # 1. Must actually be a TTY, not a pipe, file redirect, or log capture.
    try:
        if not sys.stdout.isatty():
            return False
    except (AttributeError, ValueError):
        return False

    # 2. Explicit opt-outs some tools/CI systems set.
    if os.environ.get("TERM") == "dumb":
        return False
    if os.environ.get("CI"):  # most CI runners aren't real terminals
        return False

    # 3. Windows: legacy conhost needs VT processing enabled; Windows
    #    Terminal, ConEmu, mintty, and modern conhost all advertise
    #    themselves via env vars or support it by default.
    if os.name == "nt":
        if os.environ.get("WT_SESSION"):  # Windows Terminal
            return True
        if os.environ.get("ConEmuANSI") == "ON":  # ConEmu
            return True
        if "MSYSTEM" in os.environ:  # Git Bash / MSYS2 / mintty
            return True
        # Fall back to trying to enable VT processing on conhost.
        return _enable_windows_vt_mode()

    # 4. Unix-like: presence of TERM is a reasonable signal; almost every
    #    real terminal sets it to something other than "" or "dumb".
    term = os.environ.get("TERM", "")
    return term != ""


def _enable_windows_vt_mode() -> bool:
    """Try to turn on ENABLE_VIRTUAL_TERMINAL_PROCESSING for legacy
    conhost.exe. Returns True if it succeeded (or was already on)."""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        STD_OUTPUT_HANDLE = -11
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False

        new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return bool(kernel32.SetConsoleMode(handle, new_mode))
    except Exception:
        return False


def set_title(title: str, *, force: bool = False) -> bool:
    """Set the terminal window/tab title via an OSC escape sequence.

    Returns True if the sequence was written, False if skipped because
    the terminal doesn't look compatible (override with force=True).
    """
    if not force and not _terminal_supports_title():
        return False

    sys.stdout.write(f"\x1b]0;{title}\x07")
    sys.stdout.flush()
    return True


if __name__ == "__main__":
    ok = set_title("❇ Consortium C2")
    print(f"Title set: {ok}")
    input()
