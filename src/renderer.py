"""Pygame rendering for the game view.

All drawing is done with simple primitives (rectangles, circles, lines,
text) that have direct equivalents in the MLX library.  The game logic
is never touched here: this module only reads the game state.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import pygame

from .entities import Ghost, Player
from .game import FLEE_BLINK_TIME, Level, PacmanGame
from .maze_loader import DOWN, LEFT, MazeData, UP
from .ui import FontCache

#: Classic Pac-Man palette.
COLOR_BG = (0, 0, 0)
COLOR_WALL = (33, 33, 222)
COLOR_PACGUM = (255, 184, 174)
COLOR_SUPER_PACGUM = (255, 255, 255)
COLOR_PLAYER = (255, 255, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_ACCENT = (255, 255, 0)
COLOR_EDIBLE = (33, 33, 222)
COLOR_EDIBLE_BLINK = (255, 255, 255)
COLOR_CHEAT = (255, 80, 80)

#: Ghost body colors, one per ghost index.
GHOST_COLORS: list[Tuple[int, int, int]] = [
    (255, 0, 0),       # Blinky
    (255, 184, 255),   # Pinky
    (0, 255, 255),     # Inky
    (255, 184, 82),    # Clyde
]

HUD_HEIGHT = 52
MARGIN = 14
MAX_WINDOW_WIDTH = 1280
MAX_WINDOW_HEIGHT = 720
MIN_CELL = 12
MAX_CELL = 42


class Viewport:
    """Maps maze cells to window pixels."""

    def __init__(self, maze: MazeData) -> None:
        """Compute cell size and window dimensions for a maze.

        Args:
            maze: The maze to display.
        """
        cell = max(
            MIN_CELL,
            min(
                MAX_CELL,
                (MAX_WINDOW_WIDTH - 2 * MARGIN) // maze.width,
                (MAX_WINDOW_HEIGHT - HUD_HEIGHT - 2 * MARGIN) // maze.height,
            ),
        )
        self.cell: int = cell
        self.maze_width: int = maze.width * cell
        self.maze_height: int = maze.height * cell
        self.window_width: int = self.maze_width + 2 * MARGIN
        self.window_height: int = HUD_HEIGHT + self.maze_height + 2 * MARGIN
        self.origin_x: int = MARGIN
        self.origin_y: int = HUD_HEIGHT + MARGIN

    def cell_center(self, cell: Tuple[int, int]) -> Tuple[int, int]:
        """Return the pixel center of a cell.

        Args:
            cell: Cell coordinates ``(x, y)``.

        Returns:
            Center pixel of the cell.
        """
        x, y = cell
        return (
            self.origin_x + x * self.cell + self.cell // 2,
            self.origin_y + y * self.cell + self.cell // 2,
        )

    def lerp_center(self, cell: Tuple[int, int],
                    target: Optional[Tuple[int, int]],
                    progress: float) -> Tuple[int, int]:
        """Return the pixel center between two cells.

        Args:
            cell: Current cell.
            target: Target cell of the current move.
            progress: Progress along the edge (0 to 1).

        Returns:
            Interpolated center pixel.
        """
        if target is None:
            return self.cell_center(cell)
        sx, sy = self.cell_center(cell)
        tx, ty = self.cell_center(target)
        return (
            int(round(sx + (tx - sx) * progress)),
            int(round(sy + (ty - sy) * progress)),
        )


class Renderer:
    """Draws the game view (maze, entities, HUD) on a surface."""

    def __init__(self, viewport: Viewport, fonts: FontCache) -> None:
        """Initialize the renderer for a viewport.

        Args:
            viewport: Cell-to-pixel mapping.
            fonts: Shared font cache.
        """
        self.viewport = viewport
        self.fonts = fonts
        self._walls_surface: Optional[pygame.Surface] = None
        self._walls_maze: Optional[MazeData] = None

    def draw_game(self, surface: pygame.Surface, game: PacmanGame,
                  time: float, toast: Optional[Tuple[str, float]]) -> None:
        """Draw the complete game view.

        Args:
            surface: Target surface (the window).
            game: Game state to display.
            time: Global animation clock in seconds.
            toast: Optional ``(message, remaining)`` overlay text.
        """
        level = game.level
        if level is None:
            return
        surface.fill(COLOR_BG)
        self._draw_walls(surface, level)
        self._draw_pacgums(surface, level, time)
        self._draw_super_pacgums(surface, level, time)
        for ghost in level.ghosts:
            self._draw_ghost(surface, ghost, level, time)
        self._draw_player(surface, level.player, time)
        self._draw_hud(surface, game, level)
        if level.intro_remaining > 0.0:
            self._draw_intro(surface, game)
        if toast is not None and toast[1] > 0.0:
            self._draw_toast(surface, toast[0])

    def _draw_walls(self, surface: pygame.Surface, level: Level) -> None:
        """Draw the maze walls, using a cached pre-rendered layer."""
        if self._walls_surface is None or self._walls_maze is not level.maze:
            self._walls_maze = level.maze
            self._walls_surface = self._build_wall_surface(level.maze)
        surface.blit(self._walls_surface, (self.viewport.origin_x,
                                           self.viewport.origin_y))

    def _build_wall_surface(self, maze: MazeData) -> pygame.Surface:
        """Pre-render the maze walls onto a surface.

        Args:
            maze: The maze to render.

        Returns:
            A surface with the walls drawn on a black background.
        """
        viewport = self.viewport
        surface = pygame.Surface((viewport.maze_width, viewport.maze_height))
        surface.fill(COLOR_BG)
        cell = viewport.cell
        wall = max(2, cell // 10)
        for y in range(maze.height):
            for x in range(maze.width):
                value = maze.grid[y][x]
                px = x * cell
                py = y * cell
                if value == 15:
                    pygame.draw.rect(surface, COLOR_WALL,
                                     (px, py, cell, cell))
                    continue
                if value & 1:
                    pygame.draw.rect(surface, COLOR_WALL,
                                     (px, py, cell, wall))
                if value & 2:
                    pygame.draw.rect(surface, COLOR_WALL,
                                     (px + cell - wall, py, wall, cell))
                if value & 4:
                    pygame.draw.rect(surface, COLOR_WALL,
                                     (px, py + cell - wall, cell, wall))
                if value & 8:
                    pygame.draw.rect(surface, COLOR_WALL,
                                     (px, py, wall, cell))
        return surface

    def _draw_pacgums(self, surface: pygame.Surface, level: Level,
                      time: float) -> None:
        """Draw the remaining pacgums."""
        radius = max(2, self.viewport.cell // 8)
        pulse = 1.0 + 0.15 * math.sin(time * 6.0)
        for cell in level.pacgums:
            center = self.viewport.cell_center(cell)
            pygame.draw.circle(surface, COLOR_PACGUM, center,
                               int(radius * pulse))

    def _draw_super_pacgums(self, surface: pygame.Surface, level: Level,
                            time: float) -> None:
        """Draw the remaining super-pacgums (blinking)."""
        radius = max(4, self.viewport.cell // 4)
        visible = int(time * 2.5) % 2 == 0
        if not visible:
            return
        for cell in level.super_pacgums:
            center = self.viewport.cell_center(cell)
            pygame.draw.circle(surface, COLOR_SUPER_PACGUM, center, radius)

    def _draw_player(self, surface: pygame.Surface, player: Player,
                     time: float) -> None:
        """Draw the player, blinking while protected after respawn."""
        if (player.spawn_protection > 0.0 and int(time * 8) % 2 == 0):
            return
        center = self.viewport.lerp_center(
            player.cell, player.target_cell, player.progress
        )
        radius = max(6, int(self.viewport.cell * 0.4))
        pygame.draw.circle(surface, COLOR_PLAYER, center, radius)
        if player.direction != (0, 0):
            angle = _direction_angle(player.direction)
            spread = 0.42
            p1 = (center[0] + int(radius * 1.1 * math.cos(angle - spread)),
                  center[1] + int(radius * 1.1 * math.sin(angle - spread)))
            p2 = (center[0] + int(radius * 1.1 * math.cos(angle + spread)),
                  center[1] + int(radius * 1.1 * math.sin(angle + spread)))
            pygame.draw.polygon(surface, COLOR_BG, [center, p1, p2])

    def _draw_ghost(self, surface: pygame.Surface, ghost: Ghost,
                    level: Level, time: float) -> None:
        """Draw a ghost according to its current mode."""
        center = self.viewport.lerp_center(
            ghost.cell, ghost.target_cell, ghost.progress
        )
        radius = max(6, int(self.viewport.cell * 0.42))
        if ghost.mode == "eaten":
            self._draw_ghost_eyes(surface, center, radius, ghost.direction)
            return
        if ghost.mode == "flee":
            blinking = (level.flee_remaining < FLEE_BLINK_TIME
                        and int(time * 6) % 2 == 0)
            color = COLOR_EDIBLE_BLINK if blinking else COLOR_EDIBLE
            pygame.draw.circle(surface, color, center, radius)
            return
        pygame.draw.circle(surface, GHOST_COLORS[ghost.index], center, radius)
        self._draw_ghost_eyes(surface, center, radius, ghost.direction)

    def _draw_ghost_eyes(self, surface: pygame.Surface,
                         center: Tuple[int, int], radius: int,
                         direction: Tuple[int, int]) -> None:
        """Draw the two ghost eyes with pupils looking along *direction*."""
        dx, dy = direction
        left = (center[0] - radius // 3, center[1] - radius // 6)
        right = (center[0] + radius // 3, center[1] - radius // 6)
        for eye in (left, right):
            pygame.draw.circle(surface, (255, 255, 255), eye,
                               max(2, radius // 3))
            pupil = (eye[0] + int(dx * radius * 0.12),
                     eye[1] + int(dy * radius * 0.12))
            pygame.draw.circle(surface, (33, 33, 222), pupil,
                               max(1, radius // 6))

    def _draw_hud(self, surface: pygame.Surface, game: PacmanGame,
                  level: Level) -> None:
        """Draw the in-game HUD (score, lives, level, time)."""
        pygame.draw.rect(surface, COLOR_BG, (0, 0, surface.get_width(),
                                             HUD_HEIGHT))
        pygame.draw.rect(surface, COLOR_WALL, (0, HUD_HEIGHT - 2,
                                               surface.get_width(), 2))
        font = self.fonts.get(22)
        surface.blit(font.render(f"SCORE {game.score:06d}", True,
                                 COLOR_TEXT), (12, 14))
        life_x = 200
        life_label = font.render("LIVES", True, COLOR_TEXT)
        surface.blit(life_label, (life_x, 14))
        for index in range(max(0, game.lives)):
            pygame.draw.circle(
                surface, COLOR_PLAYER,
                (life_x + life_label.get_width() + 16 + index * 20, 26), 7,
            )
        surface.blit(
            font.render(
                f"LEVEL {game.level_index + 1}/{game.level_count}", True,
                COLOR_TEXT,
            ),
            (360, 14),
        )
        time_text = font.render(
            f"TIME {max(0, int(level.time_left))}", True, COLOR_TEXT
        )
        surface.blit(time_text,
                     (surface.get_width() - time_text.get_width() - 12, 14))
        if game.cheats.active:
            cheat_text = font.render("CHEAT MODE", True, COLOR_CHEAT)
            surface.blit(
                cheat_text,
                (surface.get_width() - time_text.get_width() - 150, 14),
            )

    def _draw_intro(self, surface: pygame.Surface, game: PacmanGame) -> None:
        """Draw the "LEVEL N" banner shown at the start of a level."""
        font = self.fonts.get(44)
        text = font.render(
            f"LEVEL {game.level_index + 1}", True, COLOR_ACCENT
        )
        sub_font = self.fonts.get(20)
        sub = sub_font.render("Get ready!", True, COLOR_TEXT)
        cx = surface.get_width() // 2
        cy = HUD_HEIGHT + (surface.get_height() - HUD_HEIGHT) // 2
        box = pygame.Surface((max(text.get_width(), sub.get_width()) + 80,
                              120), pygame.SRCALPHA)
        box.fill((0, 0, 0, 190))
        surface.blit(box, (cx - box.get_width() // 2, cy - 60))
        surface.blit(text, (cx - text.get_width() // 2, cy - 48))
        surface.blit(sub, (cx - sub.get_width() // 2, cy + 8))

    def _draw_toast(self, surface: pygame.Surface, message: str) -> None:
        """Draw a transient message near the bottom of the screen."""
        font = self.fonts.get(22)
        text = font.render(message, True, COLOR_ACCENT)
        cx = surface.get_width() // 2
        cy = surface.get_height() - 40
        surface.blit(text, (cx - text.get_width() // 2, cy))


def _direction_angle(direction: Tuple[int, int]) -> float:
    """Return the movement angle of a direction vector.

    Args:
        direction: One of UP, DOWN, LEFT, RIGHT.

    Returns:
        Angle in radians.
    """
    if direction == UP:
        return -math.pi / 2
    if direction == DOWN:
        return math.pi / 2
    if direction == LEFT:
        return math.pi
    return 0.0
