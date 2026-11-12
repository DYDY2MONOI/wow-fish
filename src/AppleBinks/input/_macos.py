"""macOS keyboard injection through Quartz CGEvent."""

from __future__ import annotations

import sys
import time

from AppleBinks.capture import WindowRef
from AppleBinks.errors import InputUnavailable
from AppleBinks.input.keys import is_supported_key, normalize_key

MACOS_KEYCODES: dict[str, int] = {
    "a": 0x00,
    "s": 0x01,
    "d": 0x02,
    "f": 0x03,
    "h": 0x04,
    "g": 0x05,
    "z": 0x06,
    "x": 0x07,
    "c": 0x08,
    "v": 0x09,
    "b": 0x0B,
    "q": 0x0C,
    "w": 0x0D,
    "e": 0x0E,
    "r": 0x0F,
    "y": 0x10,
    "t": 0x11,
    "1": 0x12,
    "2": 0x13,
    "3": 0x14,
    "4": 0x15,
    "6": 0x16,
    "5": 0x17,
    "=": 0x18,
    "9": 0x19,
    "7": 0x1A,
    "-": 0x1B,
    "8": 0x1C,
    "0": 0x1D,
    "]": 0x1E,
    "o": 0x1F,
    "u": 0x20,
    "[": 0x21,
    "i": 0x22,
    "p": 0x23,
    "l": 0x25,
    "j": 0x26,
    "'": 0x27,
    "k": 0x28,
    ";": 0x29,
    "\\": 0x2A,
    ",": 0x2B,
    "/": 0x2C,
    "n": 0x2D,
    "m": 0x2E,
    ".": 0x2F,
    "`": 0x32,
    "enter": 0x24,
    "tab": 0x30,
    "space": 0x31,
    "escape": 0x35,
    "f1": 0x7A,
    "f2": 0x78,
    "f3": 0x63,
    "f4": 0x76,
    "f5": 0x60,
    "f6": 0x61,
    "f7": 0x62,
    "f8": 0x64,
    "f9": 0x65,
    "f10": 0x6D,
    "f11": 0x67,
    "f12": 0x6F,
}


class MacOSInputDevice:
    def __init__(self) -> None:
        if sys.platform != "darwin":
            raise InputUnavailable("macOS input backend requires macOS")
        try:
            import Quartz  # noqa: F401
        except ImportError as e:
            raise InputUnavailable(f"pyobjc-framework-Quartz is not installed: {e}") from e

    def press_key(self, key: str, hold_s: float = 0.06) -> None:
        import Quartz

        norm = normalize_key(key)
        if not is_supported_key(norm):
            raise InputUnavailable(f"key {key!r} is not supported")
        code = MACOS_KEYCODES.get(norm)
        if code is None:
            raise InputUnavailable(f"no macOS keycode mapping for {key!r}")

        event_down = Quartz.CGEventCreateKeyboardEvent(None, code, True)
        event_up = Quartz.CGEventCreateKeyboardEvent(None, code, False)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        time.sleep(hold_s)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)

    def is_game_focused(self, window: WindowRef) -> bool | None:
        if window.pid is None:
            return None
        try:
            from AppKit import NSWorkspace

            front = NSWorkspace.sharedWorkspace().frontmostApplication()
            if front is None:
                return None
            return front.processIdentifier() == window.pid
        except Exception:
            return None
