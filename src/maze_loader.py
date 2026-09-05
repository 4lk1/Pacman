"""Adapter around the external A-Maze-ing ``mazegenerator`` package.

The assigned A-Maze-ing package is used exactly as shipped: it is never
modified, and this module adapts to *its* interface.  ``MazeGenerator``
is always created with ``perfect=False`` so that the resulting maze has
the loops and multiple paths Pac-Man needs.

Wall encoding used by the package (bit set means the wall exists):

- North wall: bit 0 (value 1)
- East wall:  bit 1 (value 2)
- South wall: bit 2 (value 4)
- West wall:  bit 3 (value 8)

A cell holding the value ``15`` (all four walls) is a solid pillar that
the player can never enter (the ``'42'`` pattern and sealed cells).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

from mazegenerator import MazeGenerator

logger = logging.getLogger(__name__)

#: Type alias for a direction vector (dx, dy).
Direction = Tuple[int, int]

#: Direction vectors: (dx, dy).
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

#: Wall bit associated with each direction.
_DIRECTION_BITS: dict[Tuple[int, int], int] = {
    UP: 1,
    RIGHT: 2,
    DOWN: 4,
    LEFT: 8,
}

#: All four directions, in a stable order.
DIRECTIONS: Tuple[Tuple[int, int], ...] = (UP, RIGHT, DOWN, LEFT)

#: Value of a fully sealed cell (solid wall pillar).
SEALED_CELL = 15

#: How many times maze generation is retried before giving up.
_MAX_GENERATION_ATTEMPTS = 3


class MazeError(Exception):
    """Raised when the A-Maze-ing package cannot produce a maze."""


@dataclass
class MazeData:
    """Internal representation of a generated maze.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        grid: Raw ``grid[y][x]`` values from the A-Maze-ing package.
        seed: Seed used to generate this maze (0 means random).
    """

    width: int
    height: int
    grid: list[list[int]]
    seed: int


def generate_maze(width: int, height: int, seed: int) -> MazeData:
    """Generate a maze using the A-Maze-ing package.

    ``perfect`` is always set to ``False`` to produce Pac-Man-compatible
    corridors.  On failure the generation is retried with a random seed;
    if the package keeps failing a :class:`MazeError` is raised so the
    caller can report the problem cleanly.

    Args:
        width: Maze width in cells.
        height: Maze height in cells.
        seed: Fixed seed for reproducible mazes (0 means fully random).

    Returns:
        The generated :class:`MazeData`.

    Raises:
        MazeError: If the generator fails on every attempt.
    """
    attempts = _MAX_GENERATION_ATTEMPTS
    for attempt in range(attempts):
        try:
            generator = MazeGenerator(
                size=(width, height),
                perfect=False,
                seed=seed,
            )
            grid = generator.maze
            if _validate_grid(grid, width, height):
                return MazeData(
                    width=width, height=height, grid=grid, seed=seed
                )
            logger.warning(
                "MazeGenerator returned an invalid grid on attempt %d; "
                "retrying.", attempt + 1,
            )
        except Exception as error:  # noqa: BLE001 - any package failure
            logger.warning(
                "MazeGenerator failed on attempt %d (%s); retrying.",
                attempt + 1, error,
            )
        seed = 0
    raise MazeError(
        f"maze generation failed after {_MAX_GENERATION_ATTEMPTS} attempts "
        "(A-Maze-ing package error)."
    )


def _validate_grid(grid: list[list[int]], width: int, height: int) -> bool:
    """Check that the package returned a usable grid.

    Args:
        grid: Raw grid from the package.
        width: Expected width.
        height: Expected height.

    Returns:
        True if the grid has the expected shape and only valid cell
        values.
    """
    if len(grid) != height:
        return False
    for row in grid:
        if len(row) != width:
            return False
        if any(not isinstance(cell, int) or not 0 <= cell <= SEALED_CELL
               for cell in row):
            return False
    return True


def is_wall(grid: list[list[int]], x: int, y: int) -> bool:
    """Return True if the cell at ``(x, y)`` is a solid wall pillar.

    Args:
        grid: Raw maze grid.
        x: Cell column.
        y: Cell row.

    Returns:
        True when the cell cannot be entered.
    """
    return grid[y][x] == SEALED_CELL


def can_move(grid: list[list[int]], x: int, y: int,
             direction: Tuple[int, int]) -> bool:
    """Return True when the entity at ``(x, y)`` can move one cell.

    Movement is blocked by the wall bit stored in the current cell and
    by the maze border.

    Args:
        grid: Raw maze grid.
        x: Current cell column.
        y: Current cell row.
        direction: One of :data:`UP`, :data:`DOWN`, :data:`LEFT`,
            :data:`RIGHT`.

    Returns:
        True if the neighbouring cell is reachable.
    """
    dx, dy = direction
    nx, ny = x + dx, y + dy
    if not (0 <= nx < len(grid[0]) and 0 <= ny < len(grid)):
        return False
    if grid[y][x] & _DIRECTION_BITS[direction]:
        return False
    return not is_wall(grid, nx, ny)


def neighbours(grid: list[list[int]], x: int, y: int) -> list[Tuple[int, int]]:
    """List the walkable neighbouring cells of ``(x, y)``.

    Args:
        grid: Raw maze grid.
        x: Cell column.
        y: Cell row.

    Returns:
        Walkable neighbour coordinates.
    """
    result: list[Tuple[int, int]] = []
    for dx, dy in DIRECTIONS:
        nx, ny = x + dx, y + dy
        if can_move(grid, x, y, (dx, dy)):
            result.append((nx, ny))
    return result


def nearest_walkable(grid: list[list[int]], target_x: int,
                     target_y: int) -> Tuple[int, int]:
    """Find the walkable cell closest to ``(target_x, target_y)``.

    Sealed wall cells block movement in every direction, so a graph
    search cannot escape from them; the closest walkable cell is
    therefore measured with the Manhattan distance, with ties broken
    deterministically.  This is used to place the player, the ghosts
    and the super-pacgums even when their ideal cell is a wall.

    Args:
        grid: Raw maze grid.
        target_x: Preferred column.
        target_y: Preferred row.

    Returns:
        Coordinates of the nearest walkable cell.
    """
    height = len(grid)
    width = len(grid[0])
    best: Optional[Tuple[int, int]] = None
    best_key: Optional[Tuple[int, int, int]] = None
    for y in range(height):
        for x in range(width):
            if is_wall(grid, x, y):
                continue
            distance = abs(x - target_x) + abs(y - target_y)
            key = (distance, y, x)
            if best_key is None or key < best_key:
                best = (x, y)
                best_key = key
    if best is None:
        raise MazeError("maze contains no walkable cell")
    return best


def opposite(direction: Tuple[int, int]) -> Tuple[int, int]:
    """Return the direction opposite to *direction*.

    Args:
        direction: One of :data:`UP`, :data:`DOWN`, :data:`LEFT`,
            :data:`RIGHT`.

    Returns:
        The opposite direction vector.
    """
    return (-direction[0], -direction[1])


def cell_in_bounds(grid: list[list[int]], x: int, y: int) -> bool:
    """Return True when ``(x, y)`` lies inside the grid.

    Args:
        grid: Raw maze grid.
        x: Cell column.
        y: Cell row.

    Returns:
        True if the coordinates are inside the maze.
    """
    return 0 <= x < len(grid[0]) and 0 <= y < len(grid)


def neighbours_with_directions(grid: list[list[int]], x: int,
                               y: int) -> list[Tuple[int, int, int, int]]:
    """List walkable neighbours together with their direction.

    Args:
        grid: Raw maze grid.
        x: Cell column.
        y: Cell row.

    Returns:
        List of ``(nx, ny, dx, dy)`` tuples for every walkable
        neighbour.
    """
    result: list[Tuple[int, int, int, int]] = []
    for dx, dy in DIRECTIONS:
        nx, ny = x + dx, y + dy
        if can_move(grid, x, y, (dx, dy)):
            result.append((nx, ny, dx, dy))
    return result
