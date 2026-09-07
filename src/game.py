"""Core game logic.

This module contains everything needed to play Pac-Man without any
graphics: the level (maze, pacgums, entities), scoring, ghost behavior,
time limits and game progression.  The rendering layer only reads the
state exposed here.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .ai import bfs_distances, choose_step, step_toward
from .config import GameConfig
from .entities import CheatState, Ghost, Player
from .maze_loader import (MazeData, can_move, generate_maze, is_wall,
                          nearest_walkable)

#: Duration of the "LEVEL N" intro phase (ghosts and timer are frozen).
INTRO_DURATION = 1.8

#: Last seconds of the edible phase during which ghosts blink.
FLEE_BLINK_TIME = 2.0

#: How long ghosts stay frozen after the player loses a life.
POST_DEATH_FREEZE = 1.2

#: Type alias for a cell coordinate.
Cell = Tuple[int, int]

#: Type alias for a direction vector.
Direction = Tuple[int, int]

#: Game state names.
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_VICTORY = "victory"


@dataclass
class GameEvent:
    """An event produced by the game logic for the application layer.

    Attributes:
        kind: Event type: ``pacgum``, ``super_pacgum``, ``ghost_eaten``,
            ``life_lost``, ``timeout``, ``level_completed``, ``victory``
            or ``game_over``.
        value: Score delta associated with the event.
    """

    kind: str
    value: int = 0


def _advance(cell: Cell, target: Optional[Cell], moving: bool,
             progress: float, direction: Direction, speed: float,
             dt: float) -> Tuple[Cell, Optional[Cell], bool, float, bool]:
    """Advance an entity one step along its current edge.

    Args:
        cell: Current entity cell.
        target: Target cell of the current move.
        moving: Whether the entity is currently moving.
        progress: Progress along the current edge (0 to 1).
        direction: Current movement direction.
        speed: Movement speed in cells per second.
        dt: Time step in seconds.

    Returns:
        A tuple ``(cell, target, moving, progress, arrived)`` with the
        updated state; ``arrived`` is True when the entity just reached
        its target cell.
    """
    if not moving:
        return cell, target, False, progress, False
    new_progress = progress + speed * dt
    if new_progress >= 1.0:
        assert target is not None
        return target, None, False, 0.0, True
    return cell, target, True, new_progress, False


class Level:
    """A single playable level: maze, entities and collectibles."""

    def __init__(self, maze: MazeData, config: GameConfig,
                 rng: random.Random) -> None:
        """Initialize a level from a generated maze.

        Args:
            maze: Maze produced by the A-Maze-ing package.
            config: Validated game configuration.
            rng: Random source for pacgum placement and ghost decisions.
        """
        self.maze = maze
        self.config = config
        self.rng = rng
        self.time_left: float = config.level_max_time
        self.intro_remaining: float = INTRO_DURATION
        self.post_death_freeze: float = 0.0
        self.flee_remaining: float = 0.0

        #: The four corner cells, used for super-pacgums and ghost homes.
        self.corners: List[Cell] = [
            nearest_walkable(maze.grid, 0, 0),
            nearest_walkable(maze.grid, maze.width - 1, 0),
            nearest_walkable(maze.grid, 0, maze.height - 1),
            nearest_walkable(maze.grid, maze.width - 1, maze.height - 1),
        ]
        self.super_pacgums: set[Cell] = set(self.corners)
        self.ghosts: List[Ghost] = [
            Ghost(home, index) for index, home in enumerate(self.corners)
        ]
        #: Cell the player starts from and respawns at.
        self.spawn_cell: Cell = nearest_walkable(
            maze.grid, maze.width // 2, maze.height // 2
        )
        self.player = Player(self.spawn_cell)
        self.pacgums: set[Cell] = self._place_pacgums()

    def _place_pacgums(self) -> set[Cell]:
        """Place pacgums on a percentage of the corridor cells.

        The player spawn cell and the four corner cells (which hold
        super-pacgums) never receive a pacgum.

        Returns:
            The set of cells holding a pacgum.
        """
        excluded = set(self.super_pacgums) | {self.spawn_cell}
        corridors = [
            (x, y)
            for y in range(self.maze.height)
            for x in range(self.maze.width)
            if not is_wall(self.maze.grid, x, y) and (x, y) not in excluded
        ]
        self.rng.shuffle(corridors)
        count = int(round(len(corridors) * self.config.pacgum_percent / 100.0))
        return set(corridors[:count])

    def update(self, dt: float, direction: Optional[Direction],
               cheats: CheatState) -> List[GameEvent]:
        """Advance the level by one time step.

        Args:
            dt: Time step in seconds.
            direction: Direction requested by the player this frame.
            cheats: Current cheat settings.

        Returns:
            Events produced during this step.
        """
        events: List[GameEvent] = []

        if self.intro_remaining > 0.0:
            self.intro_remaining -= dt
            return events

        self._update_player(dt, direction, cheats, events)
        if any(event.kind == "level_completed" for event in events):
            return events

        if not cheats.ghost_freeze and self.post_death_freeze <= 0.0:
            player_distances = bfs_distances(self.maze, self.player.cell)
            for ghost in self.ghosts:
                self._update_ghost(ghost, player_distances, dt)

        self._check_collisions(cheats, events)
        if any(event.kind == "life_lost" for event in events):
            self.post_death_freeze = POST_DEATH_FREEZE

        if self.flee_remaining > 0.0:
            self.flee_remaining -= dt
            if self.flee_remaining <= 0.0:
                for ghost in self.ghosts:
                    if ghost.mode == "flee":
                        ghost.mode = "chase"

        if self.post_death_freeze > 0.0:
            self.post_death_freeze -= dt
        if self.player.spawn_protection > 0.0:
            self.player.spawn_protection -= dt

        self.time_left -= dt
        if self.time_left <= 0.0:
            events.append(GameEvent("timeout"))
        return events

    def _update_player(self, dt: float, direction: Optional[Direction],
                       cheats: CheatState, events: List[GameEvent]) -> None:
        """Move the player and handle pacgum collection."""
        player = self.player
        cell, target, moving, progress, arrived = _advance(
            player.cell, player.target_cell, player.moving, player.progress,
            player.direction, player.speed(cheats), dt,
        )
        player.cell, player.target_cell = cell, target
        player.moving, player.progress = moving, progress
        if arrived:
            events.extend(self._check_eat(player.cell))
            return
        if not player.moving:
            chosen = self._choose_player_direction(direction)
            if chosen is not None:
                player.direction = chosen
                player.target_cell = (
                    player.cell[0] + chosen[0], player.cell[1] + chosen[1]
                )
                player.moving = True

    def _choose_player_direction(
            self, requested: Optional[Direction]) -> Optional[Direction]:
        """Pick the direction the player should move next.

        The requested direction wins when its neighbour is walkable,
        otherwise the player keeps its current direction when possible.

        Args:
            requested: Direction requested by the player this frame.

        Returns:
            The chosen direction, or None to stay still.
        """
        player = self.player
        if (requested is not None and can_move(
                self.maze.grid, player.cell[0], player.cell[1], requested)):
            return requested
        if (player.direction != (0, 0) and can_move(
                self.maze.grid, player.cell[0], player.cell[1],
                player.direction)):
            return player.direction
        return None

    def _check_eat(self, cell: Cell) -> List[GameEvent]:
        """Collect the pacgum or super-pacgum at *cell*, if any.

        Args:
            cell: Cell the player just arrived on.

        Returns:
            Events describing what was collected.
        """
        events: List[GameEvent] = []
        if cell in self.pacgums:
            self.pacgums.remove(cell)
            events.append(GameEvent(
                "pacgum", self.config.points_per_pacgum,
            ))
            if not self.pacgums:
                events.append(GameEvent("level_completed"))
        if cell in self.super_pacgums:
            self.super_pacgums.remove(cell)
            events.append(GameEvent(
                "super_pacgum", self.config.points_per_super_pacgum,
            ))
            self.flee_remaining = self.config.super_pacgum_duration
            for ghost in self.ghosts:
                if ghost.mode == "chase":
                    ghost.mode = "flee"
        return events

    def _update_ghost(self, ghost: Ghost,
                      player_distances: dict[Cell, int], dt: float) -> None:
        """Move one ghost using its current behavior.

        Args:
            ghost: The ghost to move.
            player_distances: BFS distances from the player's cell.
            dt: Time step in seconds.
        """
        speed = ghost.speed()
        if ghost.mode == "eaten":
            # Adapt the walking speed so the trip home lasts about
            # ``ghost_respawn_time`` seconds.
            distance = bfs_distances(self.maze, ghost.cell).get(
                ghost.home, 1
            )
            speed = max(2.0, min(12.0, distance
                                 / self.config.ghost_respawn_time))
        if not ghost.moving:
            step: Optional[Direction]
            if ghost.mode == "eaten":
                step = step_toward(self.maze, ghost.cell, ghost.home)
                if step is None:
                    # Already home: come back as a chaser.
                    ghost.reset()
                    return
            else:
                step = choose_step(
                    self.maze, ghost.cell, ghost.previous_cell,
                    player_distances, ghost.mode == "flee", self.rng,
                )
            if step is None:
                ghost.moving = False
                return
            ghost.previous_cell = ghost.cell
            ghost.direction = step
            ghost.target_cell = (
                ghost.cell[0] + step[0], ghost.cell[1] + step[1]
            )
            ghost.moving = True
        cell, target, moving, progress, arrived = _advance(
            ghost.cell, ghost.target_cell, ghost.moving, ghost.progress,
            ghost.direction, speed, dt,
        )
        ghost.cell, ghost.target_cell = cell, target
        ghost.moving, ghost.progress = moving, progress

    def _check_collisions(self, cheats: CheatState,
                          events: List[GameEvent]) -> None:
        """Handle player/ghost collisions.

        Args:
            cheats: Current cheat settings.
            events: Event list to append to.
        """
        for ghost in self.ghosts:
            if ghost.mode == "eaten" or ghost.cell != self.player.cell:
                continue
            if ghost.mode == "flee":
                events.append(GameEvent(
                    "ghost_eaten", self.config.points_per_ghost,
                ))
                ghost.mode = "eaten"
                continue
            if cheats.invincible or self.player.spawn_protection > 0.0:
                continue
            events.append(GameEvent("life_lost"))
            self.player.respawn(self.spawn_cell)
            for other in self.ghosts:
                other.reset()
            self.flee_remaining = 0.0
            return


class PacmanGame:
    """The whole game session: levels, score, lives and progression."""

    def __init__(self, config: GameConfig) -> None:
        """Start a new game session.

        Args:
            config: Validated game configuration.
        """
        self.config = config
        self.score: int = 0
        self.lives: int = config.lives
        self.level_index: int = 0
        self.state: str = STATE_PLAYING
        self.cheats = CheatState()
        self.level: Optional[Level] = None
        self.start_level(0)

    @property
    def level_count(self) -> int:
        """Return the total number of levels in the game."""
        return len(self.config.levels)

    def start_level(self, index: int) -> None:
        """Generate and start the level at *index*.

        The first level uses the fixed seed from the configuration;
        every subsequent level is generated with a random seed.

        Args:
            index: Zero-based level index.
        """
        level_config = self.config.levels[index]
        seed = self.config.seed if index == 0 else 0
        maze = generate_maze(level_config.width, level_config.height, seed)
        level_rng = random.Random(self.config.seed if index == 0 else None)
        self.level = Level(maze, self.config, level_rng)
        self.level_index = index

    def update(self, dt: float,
               direction: Optional[Direction]) -> List[GameEvent]:
        """Advance the game session by one time step.

        Args:
            dt: Time step in seconds.
            direction: Direction requested by the player this frame.

        Returns:
            Events produced during this step.
        """
        if self.state != STATE_PLAYING or self.level is None:
            return []
        events = self.level.update(dt, direction, self.cheats)
        for event in events:
            if event.kind in ("pacgum", "super_pacgum", "ghost_eaten"):
                self.score += event.value
            elif event.kind in ("life_lost", "timeout"):
                self.lives -= 1
                if self.lives <= 0:
                    self.state = STATE_GAME_OVER
                elif event.kind == "timeout":
                    self.start_level(self.level_index)
            elif event.kind == "level_completed":
                if self.level_index >= self.level_count - 1:
                    self.state = STATE_VICTORY
                else:
                    self.start_level(self.level_index + 1)
        if self.state != STATE_PLAYING:
            events.append(GameEvent(self.state))
        return events

    def add_life(self) -> None:
        """Cheat: grant the player one extra life."""
        self.lives += 1

    def skip_level(self) -> List[GameEvent]:
        """Cheat: immediately win the current level.

        Returns:
            The ``level_completed`` or ``victory`` event produced.
        """
        if self.state != STATE_PLAYING:
            return []
        if self.level_index >= self.level_count - 1:
            self.state = STATE_VICTORY
            return [GameEvent("victory")]
        self.start_level(self.level_index + 1)
        return [GameEvent("level_completed")]
