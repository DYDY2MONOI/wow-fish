from __future__ import annotations

from AppleBinks.capture import WindowRef
from AppleBinks.errors import InputUnavailable


class StubInputDevice:
    def press_key(self, key: str, hold_s: float = 0.06) -> None:
        raise InputUnavailable("input injection on this platform")

    def is_game_focused(self, window: WindowRef) -> bool | None:
        return None
