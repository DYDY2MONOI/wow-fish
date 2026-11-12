"""Screen capture boundary: find the game window and grab its pixels as BGR arrays."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from AppleBinks.errors import NotSupported

Box = tuple[int, int, int, int]  # x, y, width, height in window pixels


@dataclass(frozen=True)
class WindowRef:
    title: str
    pid: int | None
    left: int  # screen position; logical (unscaled) pixels for a Wayland window
    top: int
    width: int  # size of a grab, in pixels
    height: int
    handle: int | None = None  # native window id where the platform has one
    compositor: str | None = None  # "hyprland" for a native Wayland window, else None
    scale: float = 1.0  # the Wayland output's scale: grab pixels per logical pixel


@runtime_checkable
class Capturer(Protocol):
    def open(self, window: WindowRef) -> None: ...

    def grab(self, box: Box | None = None) -> np.ndarray:
        """Return the window (or `box` inside it) as HxWx3 uint8 BGR."""
        ...

    def close(self) -> None: ...


def linux_x11() -> bool:
    return sys.platform == "linux" and bool(os.environ.get("DISPLAY"))


def linux_hyprland() -> bool:
    return sys.platform == "linux" and bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))


def find_window(title_substring: str = "World of Warcraft") -> WindowRef | None:
    """The largest viewable window whose title contains the text.

    On Hyprland the compositor picks it from all its windows, native Wayland and Xwayland alike;
    an Xwayland winner is then looked up through X11 by its pid. Elsewhere X11, then Windows;
    else None.
    """
    pid: int | None = None
    if linux_hyprland():
        from AppleBinks.capture._wayland import find_window_hyprland

        try:
            found = find_window_hyprland(title_substring)
        except (NotSupported, OSError, ValueError):
            if not linux_x11():
                raise
            # Hyprland's IPC did not answer; X11 alone still finds an Xwayland game
        else:
            if found is None or found.compositor:
                return found
            pid = found.pid
    if linux_x11():
        from AppleBinks.capture._x11 import find_window_x11

        return find_window_x11(title_substring, pid)
    if sys.platform == "win32":
        from AppleBinks.capture import _win32

        return _win32.find_window_win32(title_substring)
    if sys.platform == "darwin":
        from AppleBinks.capture._macos import find_window_macos

        return find_window_macos(title_substring)
    return None


def get_capturer(window: WindowRef | None = None) -> Capturer:
    """The capturer for this window: Wayland's, then X11's, then macOS's window capture.

    macOS reads the window by its id, so it works even when the bot's own window is in front;
    the mss fallback (Windows, and macOS without a window id) reads a screen rectangle, so
    anything overlapping the game is what gets grabbed.
    """
    if window is not None and window.compositor:
        from AppleBinks.capture._wayland import GrimCapturer

        return GrimCapturer()
    if linux_x11():
        from AppleBinks.capture._x11 import X11WindowCapturer

        return X11WindowCapturer()
    if sys.platform == "darwin" and window is not None and window.handle is not None:
        from AppleBinks.capture._macos import MacWindowCapturer

        return MacWindowCapturer()
    try:
        import mss  # noqa: F401
    except Exception:
        from AppleBinks.capture._stub import StubCapturer

        return StubCapturer()
    from AppleBinks.capture._mss import MssCapturer

    return MssCapturer()


__all__ = [
    "Box",
    "Capturer",
    "WindowRef",
    "find_window",
    "get_capturer",
    "linux_hyprland",
    "linux_x11",
]
