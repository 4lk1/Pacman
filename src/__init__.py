"""Pac-Man source package.

Modules:
- config: JSON-with-comments configuration loading
- maze_loader: adapter for the A-Maze-ing mazegenerator package
- highscores: persistent top-10 highscore system
- ai: ghost pathfinding (BFS chase/flee)
- entities: Player, Ghost and cheat state
- game: game logic (levels, scoring, progression)
- renderer: pygame game rendering
- ui: pygame menus and screens
- main: application event loop
"""

from __future__ import annotations
