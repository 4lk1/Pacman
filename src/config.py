"""Configuration loading for Pac-Man.

The game is configured through a JSON file that may contain comments.
Lines starting with ``#`` or ``//`` are ignored, and inline comments
placed outside of string literals are stripped as well.  Every key is
optional: missing or invalid values are clamped to safe defaults while a
clear warning is logged, and unknown keys are silently ignored.  This
module never raises, so a broken configuration file can never crash the
game.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

#: Default configuration values, used when a key is absent or invalid.
DEFAULT_HIGHSCORE_FILENAME = "highscores.json"
DEFAULT_LIVES = 3
DEFAULT_PACGUM_PERCENT = 42
DEFAULT_POINTS_PER_PACGUM = 10
DEFAULT_POINTS_PER_SUPER_PACGUM = 50
DEFAULT_POINTS_PER_GHOST = 200
DEFAULT_SEED = 42
DEFAULT_LEVEL_MAX_TIME = 90
DEFAULT_SUPER_PACGUM_DURATION = 8
DEFAULT_GHOST_RESPAWN_TIME = 8
DEFAULT_LEVEL_WIDTH = 15
DEFAULT_LEVEL_HEIGHT = 15

#: Number of levels shipped in the default configuration (game requires
#: at least 10 levels).
DEFAULT_LEVELS: list[dict[str, int]] = [
    {"width": 15, "height": 15},
    {"width": 17, "height": 15},
    {"width": 19, "height": 17},
    {"width": 21, "height": 19},
    {"width": 23, "height": 15},
    {"width": 25, "height": 19},
    {"width": 27, "height": 17},
    {"width": 29, "height": 19},
    {"width": 31, "height": 15},
    {"width": 31, "height": 19},
]

#: Hard bounds applied when a value is present but out of range.
_BOUNDS: dict[str, tuple[float, float]] = {
    "lives": (1, 9),
    "pacgum": (1, 100),
    "points_per_pacgum": (0, 100000),
    "points_per_super_pacgum": (0, 100000),
    "points_per_ghost": (0, 100000),
    "seed": (0, 2147483647),
    "level_max_time": (10, 600),
    "super_pacgum_duration": (1, 30),
    "ghost_respawn_time": (1, 30),
    "level_width": (15, 60),
    "level_height": (15, 60),
}


@dataclass
class LevelConfig:
    """Dimensions of a single maze level."""

    width: int
    height: int


@dataclass
class GameConfig:
    """Validated game configuration with safe defaults applied."""

    highscore_filename: str = DEFAULT_HIGHSCORE_FILENAME
    levels: list[LevelConfig] = field(
        default_factory=lambda: [LevelConfig(**lvl) for lvl in DEFAULT_LEVELS]
    )
    lives: int = DEFAULT_LIVES
    pacgum_percent: int = DEFAULT_PACGUM_PERCENT
    points_per_pacgum: int = DEFAULT_POINTS_PER_PACGUM
    points_per_super_pacgum: int = DEFAULT_POINTS_PER_SUPER_PACGUM
    points_per_ghost: int = DEFAULT_POINTS_PER_GHOST
    seed: int = DEFAULT_SEED
    level_max_time: float = DEFAULT_LEVEL_MAX_TIME
    super_pacgum_duration: float = DEFAULT_SUPER_PACGUM_DURATION
    ghost_respawn_time: float = DEFAULT_GHOST_RESPAWN_TIME


def strip_comments(text: str) -> str:
    """Remove ``#`` and ``//`` comments from a JSON document.

    Full-line and inline comments are both supported.  Comment markers
    found inside string literals are preserved so that values containing
    ``#`` or ``//`` stay intact.

    Args:
        text: Raw content of the configuration file.

    Returns:
        The same content with every comment removed.
    """
    cleaned: list[str] = []
    for line in text.splitlines():
        output: list[str] = []
        in_string = False
        quote = ""
        index = 0
        while index < len(line):
            char = line[index]
            if in_string:
                output.append(char)
                if char == "\\" and index + 1 < len(line):
                    output.append(line[index + 1])
                    index += 2
                    continue
                if char == quote:
                    in_string = False
                index += 1
                continue
            if char in ('"', "'"):
                in_string = True
                quote = char
                output.append(char)
                index += 1
                continue
            if char == "#":
                break
            if char == "/" and index + 1 < len(line) and line[index + 1] == "/":  # noqa: E501
                break
            output.append(char)
            index += 1
        cleaned.append("".join(output))
    return "\n".join(cleaned)


def _clamp_int(value: Any, key: str, default: int, minimum: int,
               maximum: int, silent: bool = False) -> int:
    """Return *value* as an int clamped to ``[minimum, maximum]``.

    Logs a warning whenever the raw value was missing, of the wrong
    type, or out of range, and falls back to *default* or the bound.

    Args:
        value: Raw value coming from the configuration file.
        key: Name of the key, used in warning messages.
        default: Safe default used when the value is invalid.
        minimum: Lower clamp bound.
        maximum: Upper clamp bound.
        silent: When True, no warning is logged (used when the whole
            file failed to load and every key is a fallback).

    Returns:
        A safe integer.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        if not silent:
            logger.warning(
                "Config key '%s' is not an integer (%r); using default %d.",
                key, value, default,
            )
        return default
    if value < minimum:
        if not silent:
            logger.warning(
                "Config key '%s' is below %d (%d); clamped.",
                key, minimum, value,
            )
        return minimum
    if value > maximum:
        if not silent:
            logger.warning(
                "Config key '%s' is above %d (%d); clamped.",
                key, maximum, value,
            )
        return maximum
    return value


def _clamp_float(value: Any, key: str, default: float, minimum: float,
                 maximum: float, silent: bool = False) -> float:
    """Return *value* as a float clamped to ``[minimum, maximum]``.

    Args:
        value: Raw value coming from the configuration file.
        key: Name of the key, used in warning messages.
        default: Safe default used when the value is invalid.
        minimum: Lower clamp bound.
        maximum: Upper clamp bound.
        silent: When True, no warning is logged (used when the whole
            file failed to load and every key is a fallback).

    Returns:
        A safe float.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        if not silent:
            logger.warning(
                "Config key '%s' is not a number (%r); using default %s.",
                key, value, default,
            )
        return default
    number = float(value)
    if number < minimum:
        if not silent:
            logger.warning(
                "Config key '%s' is below %s (%s); clamped.",
                key, minimum, number,
            )
        return minimum
    if number > maximum:
        if not silent:
            logger.warning(
                "Config key '%s' is above %s (%s); clamped.",
                key, maximum, number,
            )
        return maximum
    return number


def _parse_levels(raw: Any, silent: bool = False) -> list[LevelConfig]:
    """Parse the ``levels`` array into a list of level configurations.

    Args:
        raw: Raw value of the ``levels`` key.
        silent: When True, no warning is logged.

    Returns:
        A non-empty list of valid level configurations.
    """
    if not isinstance(raw, list) or not raw:
        if not silent:
            logger.warning(
                "Config key 'levels' is missing or empty; using %d default "
                "levels.", len(DEFAULT_LEVELS),
            )
        return [LevelConfig(**lvl) for lvl in DEFAULT_LEVELS]
    levels: list[LevelConfig] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict):
            if not silent:
                logger.warning(
                    "Level %d is not an object (%r); using default level.",
                    index + 1, entry,
                )
            levels.append(
                LevelConfig(DEFAULT_LEVEL_WIDTH, DEFAULT_LEVEL_HEIGHT)
            )
            continue
        width = _clamp_int(
            entry.get("width"), f"levels[{index}].width",
            DEFAULT_LEVEL_WIDTH, 15, 60, silent=silent,
        )
        height = _clamp_int(
            entry.get("height"), f"levels[{index}].height",
            DEFAULT_LEVEL_HEIGHT, 15, 60, silent=silent,
        )
        levels.append(LevelConfig(width, height))
    if len(levels) < len(DEFAULT_LEVELS):
        if not silent:
            logger.warning(
                "Config key 'levels' contains %d level(s); at least %d are "
                "required. Filling the remaining levels with defaults.",
                len(levels), len(DEFAULT_LEVELS),
            )
        for index in range(len(levels), len(DEFAULT_LEVELS)):
            fallback = DEFAULT_LEVELS[index]
            levels.append(LevelConfig(**fallback))
    return levels


def _parse_highscore_filename(raw: Any, silent: bool = False) -> str:
    """Parse and validate the ``highscore_filename`` key.

    Args:
        raw: Raw value of the key.
        silent: When True, no warning is logged.

    Returns:
        A non-empty filename string.
    """
    if not isinstance(raw, str) or not raw.strip():
        if not silent:
            logger.warning(
                "Config key 'highscore_filename' is invalid (%r); using "
                "default '%s'.", raw, DEFAULT_HIGHSCORE_FILENAME,
            )
        return DEFAULT_HIGHSCORE_FILENAME
    return raw.strip()


def load_config(path: str) -> GameConfig:
    """Load and validate the configuration file at *path*.

    The file is parsed as JSON after comments are stripped.  Any error
    (missing file, invalid JSON, missing or invalid keys) is logged with
    a clear message and safe defaults are used instead, so this function
    never raises.

    Args:
        path: Path to the ``.json`` configuration file.

    Returns:
        A validated :class:`GameConfig` instance.
    """
    raw_data: dict[str, Any] = {}
    file_loaded = True
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        raw_data = json.loads(strip_comments(content))
        if not isinstance(raw_data, dict):
            logger.warning(
                "Configuration file '%s' does not contain a JSON object "
                "(%r); using default configuration.", path, raw_data,
            )
            raw_data = {}
    except FileNotFoundError:
        logger.warning(
            "Configuration file '%s' not found; using default "
            "configuration.", path,
        )
        file_loaded = False
    except (OSError, json.JSONDecodeError) as error:
        logger.warning(
            "Could not read configuration file '%s' (%s); using default "
            "configuration.", path, error,
        )
        file_loaded = False

    silent = not file_loaded
    config = GameConfig(
        highscore_filename=_parse_highscore_filename(
            raw_data.get("highscore_filename"), silent=silent
        ),
        levels=_parse_levels(raw_data.get("levels"), silent=silent),
        lives=_clamp_int(raw_data.get("lives"), "lives", DEFAULT_LIVES, 1, 9,
                         silent=silent),
        pacgum_percent=_clamp_int(
            raw_data.get("pacgum"), "pacgum", DEFAULT_PACGUM_PERCENT, 1, 100,
            silent=silent,
        ),
        points_per_pacgum=_clamp_int(
            raw_data.get("points_per_pacgum"), "points_per_pacgum",
            DEFAULT_POINTS_PER_PACGUM, 0, 100000, silent=silent,
        ),
        points_per_super_pacgum=_clamp_int(
            raw_data.get("points_per_super_pacgum"),
            "points_per_super_pacgum", DEFAULT_POINTS_PER_SUPER_PACGUM,
            0, 100000, silent=silent,
        ),
        points_per_ghost=_clamp_int(
            raw_data.get("points_per_ghost"), "points_per_ghost",
            DEFAULT_POINTS_PER_GHOST, 0, 100000, silent=silent,
        ),
        seed=_clamp_int(
            raw_data.get("seed"), "seed", DEFAULT_SEED, 0, 2147483647,
            silent=silent,
        ),
        level_max_time=_clamp_float(
            raw_data.get("level_max_time"), "level_max_time",
            DEFAULT_LEVEL_MAX_TIME, 10, 600, silent=silent,
        ),
        super_pacgum_duration=_clamp_float(
            raw_data.get("super_pacgum_duration"), "super_pacgum_duration",
            DEFAULT_SUPER_PACGUM_DURATION, 1, 30, silent=silent,
        ),
        ghost_respawn_time=_clamp_float(
            raw_data.get("ghost_respawn_time"), "ghost_respawn_time",
            DEFAULT_GHOST_RESPAWN_TIME, 1, 30, silent=silent,
        ),
    )
    return config
