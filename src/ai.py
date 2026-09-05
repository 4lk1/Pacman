"""Ghost artificial intelligence.

The chase behavior is distance-based: every ghost moves toward the cell
that minimizes its distance to the player (computed with a breadth-first
search over the corridor graph).  When the ghosts are edible they run
away, picking the neighbouring cell that maximizes the distance to the
player.  All decisions are made when a ghost reaches a cell centre.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Dict, List, Tuple

from .maze_loader import MazeData, can_move, DIRECTIONS

#: Type alias for a cell coordinate.
Cell = Tuple[int, int]

#: Type alias for a direction vector.
Direction = Tuple[int, int]


def bfs_distances(maze: MazeData, start: Cell) -> Dict[Cell, int]:
    """Compute the distance from *start* to every walkable cell.

    Args:
        maze: The maze the ghost is moving through.
        start: Cell to measure distances from.

    Returns:
        Mapping of cell -> shortest corridor distance from *start*.
    """
    distances: Dict[Cell, int] = {start: 0}
    queue: deque[Cell] = deque([start])
    while queue:
        x, y = queue.popleft()
        distance = distances[(x, y)]
        for nx, ny in _walkable_neighbours(maze, x, y):
            if (nx, ny) not in distances:
                distances[(nx, ny)] = distance + 1
                queue.append((nx, ny))
    return distances


def _walkable_neighbours(maze: MazeData, x: int, y: int) -> List[Cell]:
    """List the walkable neighbours of a cell.

    Args:
        maze: The maze the ghost is moving through.
        x: Cell column.
        y: Cell row.

    Returns:
        Walkable neighbour coordinates.
    """
    result: List[Cell] = []
    for dx, dy in DIRECTIONS:
        nx, ny = x + dx, y + dy
        if can_move(maze.grid, x, y, (dx, dy)):
            result.append((nx, ny))
    return result


def choose_step(maze: MazeData, cell: Cell, previous: Cell | None,
                player_distances: Dict[Cell, int],
                flee: bool, rng: random.Random) -> Direction | None:
    """Choose the next direction for a ghost standing at *cell*.

    When chasing (``flee`` is False) the ghost picks the neighbour with
    the smallest distance to the player; when fleeing it picks the
    neighbour with the largest distance.  Ties are broken randomly, and
    the ghost avoids turning back the way it came unless it is trapped
    in a dead end.

    Args:
        maze: The maze the ghost is moving through.
        cell: Current ghost cell.
        previous: The cell the ghost came from (None at spawn).
        player_distances: BFS distances from the player's cell.
        flee: True when the ghost is edible and must run away.
        rng: Random source used for tie-breaking.

    Returns:
        The chosen direction, or None when no move is possible.
    """
    candidates: List[Cell] = _walkable_neighbours(maze, cell[0], cell[1])
    if not candidates:
        return None
    if previous is not None and len(candidates) > 1:
        candidates = [c for c in candidates if c != previous]

    def distance_key(cell_: Cell) -> int:
        return player_distances.get(cell_, 10 ** 9)

    if flee:
        best = max(distance_key(c) for c in candidates)
    else:
        best = min(distance_key(c) for c in candidates)
    best_cells = [c for c in candidates if distance_key(c) == best]
    target = rng.choice(best_cells)
    return (target[0] - cell[0], target[1] - cell[1])


def step_toward(maze: MazeData, start: Cell, target: Cell) -> Direction | None:
    """Return the first step of the shortest path from *start* to target.

    Used by eaten ghosts to find their way back to their corner.

    Args:
        maze: The maze the ghost is moving through.
        start: Current ghost cell.
        target: Destination cell.

    Returns:
        The direction of the first step, or None when the target is
        unreachable or already reached.
    """
    if start == target:
        return None
    parents: Dict[Cell, Cell | None] = {start: None}
    queue: deque[Cell] = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in _walkable_neighbours(maze, x, y):
            if (nx, ny) in parents:
                continue
            parents[(nx, ny)] = (x, y)
            if (nx, ny) == target:
                queue.clear()
                break
            queue.append((nx, ny))
    if target not in parents:
        return None
    current = target
    while parents[current] != start:
        parent = parents[current]
        if parent is None:
            return None
        current = parent
    return (current[0] - start[0], current[1] - start[1])
