"""Pac-Man — game entry point.

Usage:
    python3 pac-man.py config.json

The program takes exactly one argument: a JSON configuration file.
Every error is reported with a clear message on stderr and a non-zero
exit code, never with a Python traceback.
"""

from __future__ import annotations

import logging
import sys
from typing import List

USAGE = "Usage: python3 pac-man.py config.json"


def _fail(message: str) -> int:
    """Print an error message and return a non-zero exit code.

    Args:
        message: Message to print on stderr.

    Returns:
        Exit code 1.
    """
    print(f"Error: {message}", file=sys.stderr)
    return 1


def main(argv: List[str]) -> int:
    """Run the game with the command line arguments.

    Args:
        argv: Command line arguments (without the program name).

    Returns:
        Process exit code.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    if len(argv) != 1:
        print(USAGE, file=sys.stderr)
        return 1
    config_path = argv[0]
    if not config_path.endswith(".json"):
        return _fail(
            f"'{config_path}' is not a JSON file: the configuration file "
            "must end with '.json'."
        )
    try:
        import mazegenerator  # noqa: F401 - import check only
    except ImportError:
        return _fail(
            "the A-Maze-ing 'mazegenerator' package is not installed. "
            "Run 'make install' to install it from the provided wheel."
        )
    try:
        from src.config import load_config
        from src.main import PacmanApp
    except ImportError as error:
        return _fail(
            f"missing dependency ({error}). Run 'make install' first."
        )
    try:
        config = load_config(config_path)
        app = PacmanApp(config)
        app.run()
    except KeyboardInterrupt:
        return 0
    except Exception as error:  # noqa: BLE001 - never show a traceback
        return _fail(f"unexpected error: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
