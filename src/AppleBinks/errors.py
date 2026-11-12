"""Exceptions shared across AppleBinks."""


class NotSupported(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(f"AppleBinks does not support {detail} yet.")


class InputUnavailable(NotSupported):
    """No way to press keys on this platform or display."""
