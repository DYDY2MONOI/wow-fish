"""macOS window lookup and capture through Quartz: the largest visible window whose title
matches, and its own pixels even when another window (the bot's own) covers it."""

from __future__ import annotations

import sys
from typing import Any

import numpy as np

from AppleBinks.capture import Box, WindowRef


def find_window_macos(title_substring: str = "World of Warcraft") -> WindowRef | None:
    if sys.platform != "darwin":
        return None
    try:
        import Quartz
    except ImportError:
        return None

    wanted = title_substring.lower()
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID
    )
    found: list[WindowRef] = []
    for w in windows:
        owner = str(w.get("kCGWindowOwnerName") or "")
        name = str(w.get("kCGWindowName") or "")
        match = (
            wanted in owner.lower()
            or wanted in name.lower()
            or ("warcraft" in wanted and owner.lower() == "wow")
        )
        if match:
            bounds = w.get("kCGWindowBounds", {})
            pid = w.get("kCGWindowOwnerPID")
            wid = w.get("kCGWindowNumber")
            x = int(bounds.get("X", 0))
            y = int(bounds.get("Y", 0))
            width = int(bounds.get("Width", 0))
            height = int(bounds.get("Height", 0))
            if width > 100 and height > 100:
                found.append(
                    WindowRef(
                        title=name or owner,
                        pid=int(pid) if pid else None,
                        left=x,
                        top=y,
                        width=width,
                        height=height,
                        handle=int(wid) if wid else None,
                    )
                )
    if not found:
        return None
    return max(found, key=lambda r: r.width * r.height)


def _quartz() -> Any:
    import Quartz

    return Quartz


def grab_window(handle: int) -> np.ndarray:
    """The window's own pixels as HxWx3 BGR, whatever is drawn on top of it.

    `kCGWindowImageNominalResolution` keeps the capture in window points, the same size as
    `WindowRef.width` x `WindowRef.height`, so a Retina screen does not double the coordinates
    the engine tracks in.
    """
    Quartz = _quartz()
    options = (
        Quartz.kCGWindowImageBoundsIgnoreFraming
        | Quartz.kCGWindowImageShouldBeOpaque
        | Quartz.kCGWindowImageNominalResolution
    )
    image = Quartz.CGWindowListCreateImage(
        Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow, handle, options
    )
    if image is None:
        raise RuntimeError(
            "macOS will not capture the game window: it closed, or AppleBinks is not allowed "
            "Screen Recording (System Settings > Privacy & Security)"
        )
    width = int(Quartz.CGImageGetWidth(image))
    height = int(Quartz.CGImageGetHeight(image))
    data = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(image))
    stride = int(Quartz.CGImageGetBytesPerRow(image))
    pixel = max(1, (int(Quartz.CGImageGetBitsPerPixel(image)) + 7) // 8)
    raw = np.frombuffer(bytes(data), dtype=np.uint8)
    packed = raw.reshape(height, stride)[:, : width * pixel]
    return np.ascontiguousarray(packed.reshape(height, width, pixel)[:, :, :3])  # BGRA -> BGR


class MacWindowCapturer:
    """Grabs one window's pixels by id, so a window in front of the game does not hide it."""

    def __init__(self) -> None:
        self._window: WindowRef | None = None

    def open(self, window: WindowRef) -> None:
        if window.handle is None:
            raise ValueError("macOS capture needs WindowRef.handle (use find_window)")
        self._window = window

    def grab(self, box: Box | None = None) -> np.ndarray:
        if self._window is None:
            raise RuntimeError("capturer is not open")
        frame = grab_window(self._window.handle)
        width, height = self._window.width, self._window.height
        if frame.shape[1] != width or frame.shape[0] != height:  # clipped or scaled window
            import cv2

            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        x, y, w, h = box or (0, 0, width, height)
        x, y = max(0, x), max(0, y)
        w, h = max(0, min(w, width - x)), max(0, min(h, height - y))
        return np.ascontiguousarray(frame[y : y + h, x : x + w])

    def close(self) -> None:
        self._window = None
