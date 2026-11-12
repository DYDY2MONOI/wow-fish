"""Entry point for the windowed `AppleBinks-gui` executable: `AppleBinks gui`, no console."""

import sys

from AppleBinks.cli import main

if __name__ == "__main__":
    if "--version" not in sys.argv[1:]:
        sys.argv = [sys.argv[0], "gui", *sys.argv[1:]]
    main()
