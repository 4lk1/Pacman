"""Persistent highscore system.

Highscores are stored in a JSON file on disk (path configurable through
the ``highscore_filename`` configuration key).  The table keeps the top
10 entries, each made of a player name and a non-negative integer score.
The file is loaded when the game starts and saved when it ends, and the
loader is robust against missing or corrupted files.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

#: Maximum number of entries kept in the highscore table.
MAX_ENTRIES = 10

#: Maximum length of a player name.
MAX_NAME_LENGTH = 10

#: Accepted characters: alphanumeric and spaces only.
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 ]+$")

#: Names are trimmed to this length when saved.
_TRIM_NAME_LENGTH = 10


@dataclass(frozen=True)
class ScoreEntry:
    """A single highscore entry."""

    name: str
    score: int


def validate_name(name: str) -> str | None:
    """Validate a player name.

    A valid name has at most :data:`MAX_NAME_LENGTH` characters and only
    contains alphanumeric characters and spaces.

    Args:
        name: The name typed by the player.

    Returns:
        The cleaned name when valid, or None when it is not.
    """
    cleaned = name.strip()
    if not cleaned or len(cleaned) > _TRIM_NAME_LENGTH:
        return None
    if not _NAME_PATTERN.fullmatch(cleaned):
        return None
    return cleaned


def validate_score(score: Any) -> int | None:
    """Validate a score value.

    Args:
        score: Raw score read from a file or supplied by the game.

    Returns:
        The score as a non-negative int, or None when invalid.
    """
    if isinstance(score, bool) or not isinstance(score, int):
        return None
    if score < 0:
        return None
    return score


class HighscoreTable:
    """An ordered collection of the top 10 highscores.

    Attributes:
        entries: Current entries, sorted by score descending.
    """

    def __init__(self, entries: list[ScoreEntry] | None = None) -> None:
        """Initialize the table, optionally from existing entries."""
        self.entries: list[ScoreEntry] = list(entries or [])
        self._sort_and_trim()

    def _sort_and_trim(self) -> None:
        """Keep the table sorted (descending) and capped at 10 entries."""
        self.entries.sort(key=lambda entry: entry.score, reverse=True)
        self.entries = self.entries[:MAX_ENTRIES]

    def add(self, name: str, score: Any) -> bool:
        """Insert a validated entry into the table.

        Invalid entries are rejected with a logged warning.

        Args:
            name: Player name (validated with :func:`validate_name`).
            score: Non-negative integer score (any value is validated).

        Returns:
            True when the entry was added to the table.
        """
        cleaned_name = validate_name(name)
        cleaned_score = validate_score(score)
        if cleaned_name is None or cleaned_score is None:
            logger.warning(
                "Rejected invalid highscore entry (name=%r, score=%r).",
                name, score,
            )
            return False
        self.entries.append(ScoreEntry(cleaned_name, cleaned_score))
        self._sort_and_trim()
        return True

    def top(self) -> list[ScoreEntry]:
        """Return a copy of the current top 10 entries.

        Returns:
            Entries sorted by score, highest first.
        """
        return list(self.entries)

    def save(self, path: str) -> bool:
        """Write the table to a JSON file on disk.

        Args:
            path: Destination file path.

        Returns:
            True on success, False when the file could not be written.
        """
        payload = {
            "highscores": [
                {"name": entry.name, "score": entry.score}
                for entry in self.entries
            ]
        }
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except OSError as error:
            logger.warning("Could not save highscores to '%s' (%s).", path,
                           error)
            return False
        return True

    @classmethod
    def load(cls, path: str) -> "HighscoreTable":
        """Load the table from a JSON file.

        Missing files, corrupted content and invalid entries are handled
        gracefully: warnings are logged and the table starts empty.

        Args:
            path: Source file path.

        Returns:
            A populated :class:`HighscoreTable`.
        """
        table = cls()
        if not os.path.exists(path):
            logger.info("No highscore file at '%s'; starting empty.", path)
            return table
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as error:
            logger.warning(
                "Could not read highscore file '%s' (%s); starting "
                "empty.", path, error,
            )
            return table
        if not isinstance(payload, dict):
            logger.warning(
                "Highscore file '%s' has an invalid format; starting "
                "empty.", path,
            )
            return table
        raw_entries = payload.get("highscores")
        if not isinstance(raw_entries, list):
            logger.warning(
                "Highscore file '%s' has no 'highscores' list; starting "
                "empty.", path,
            )
            return table
        for raw in raw_entries:
            if not isinstance(raw, dict):
                logger.warning(
                    "Dropping invalid highscore entry in '%s': %r.",
                    path, raw,
                )
                continue
            name = raw.get("name")
            score = raw.get("score")
            if not isinstance(name, str) or not table.add(name, score):
                logger.warning(
                    "Dropping invalid highscore entry in '%s': %r.",
                    path, raw,
                )
        return table
