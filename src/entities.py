"""Game entities: the player (Pac-Man) and the ghosts.

Entities move on the cell grid.  Movement between two adjacent cells is
smoothed with a ``progress`` value in ``[0, 1]``: when ``progress``
reaches 1 the entity arrives at its target cell and a new step can be
chosen.  This keeps the game logic independent from any rendering code.
"""

from __future__ import annotations

from typing import Tuple

from .maze_loader import Direction

#: Movement speeds in cells per second.
PLAYER_SPEED = 4.4
GHOST_CHASE_SPEED = 3.8
GHOST_FLEE_SPEED = 2.4
GHOST_EATEN_SPEED = 7.0
CHEAT_SPEED_MULTIPLIER = 1.6

#: How long the player is protected right after respawning (seconds).
SPAWN_PROTECTION_TIME = 2.0

#: How long ghosts stay frozen after the player loses a life.
POST_DEATH_FREEZE_TIME = 1.2


class Player:
    """The player-controlled character."""

    def __init__(self, cell: Tuple[int, int]) -> None:
        """Initialize the player.

        Args:
            cell: Spawn cell (middle of the maze).
        """
        self.cell: Tuple[int, int] = cell
        self.direction: Direction = (0, 0)
        self.target_cell: Tuple[int, int] | None = None
        self.progress: float = 0.0
        self.moving: bool = False
        self.spawn_protection: float = 0.0

    def respawn(self, cell: Tuple[int, int]) -> None:
        """Move the player back to *cell* and grant spawn protection.

        Args:
            cell: Respawn cell (middle of the maze).
        """
        self.cell = cell
        self.direction = (0, 0)
        self.target_cell = None
        self.progress = 0.0
        self.moving = False
        self.spawn_protection = SPAWN_PROTECTION_TIME

    def speed(self, cheats: "CheatState") -> float:
        """Return the effective movement speed.

        Args:
            cheats: Current cheat settings.

        Returns:
            Speed in cells per second.
        """
        if cheats.speed:
            return PLAYER_SPEED * CHEAT_SPEED_MULTIPLIER
        return PLAYER_SPEED


class Ghost:
    """An autonomous ghost."""

    def __init__(self, home: Tuple[int, int], index: int) -> None:
        """Initialize the ghost at its home corner.

        Args:
            home: Corner cell the ghost spawns in and returns to.
            index: Ghost index (0-3), used for coloring.
        """
        self.home: Tuple[int, int] = home
        self.index: int = index
        self.cell: Tuple[int, int] = home
        self.direction: Direction = (0, 0)
        self.target_cell: Tuple[int, int] | None = None
        self.progress: float = 0.0
        self.moving: bool = False
        self.previous_cell: Tuple[int, int] | None = None
        #: One of "chase", "flee", "eaten".
        self.mode: str = "chase"
        self.frozen: bool = False

    def reset(self) -> None:
        """Send the ghost back to its home corner in chase mode."""
        self.cell = self.home
        self.direction = (0, 0)
        self.target_cell = None
        self.progress = 0.0
        self.moving = False
        self.previous_cell = None
        self.mode = "chase"
        self.frozen = False

    def speed(self) -> float:
        """Return the movement speed for the current mode.

        Returns:
            Speed in cells per second.
        """
        if self.mode == "flee":
            return GHOST_FLEE_SPEED
        if self.mode == "eaten":
            return GHOST_EATEN_SPEED
        return GHOST_CHASE_SPEED


class CheatState:
    """Cheat flags toggled through the in-game cheat menu.

    Attributes:
        invincible: Ghosts cannot eat the player.
        ghost_freeze: Ghosts stop moving.
        speed: The player moves faster.
    """

    def __init__(self) -> None:
        """Initialize all cheats as disabled."""
        self.invincible: bool = False
        self.ghost_freeze: bool = False
        self.speed: bool = False

    @property
    def active(self) -> bool:
        """Return True when at least one cheat is enabled."""
        return self.invincible or self.ghost_freeze or self.speed
