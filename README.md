*This activity has been created as part of the 42 curriculum by aleka, gkordhak.*

# Pac-Man — Ghosts! More ghosts!

## Description

This project recreates the famous arcade game Pac-Man in Python. The game
features procedurally generated mazes (produced by an external A-Maze-ing
package assigned at project start), a persistent highscore system, multiple
levels with increasing difficulty, four ghosts with distance-based chase and
flee behaviors, and a cheat mode designed to make peer review easy.

The game follows the classic loop: **Main Menu > start game > Win or Lose >
Enter name for highscore > Back to Main Menu**.

## Instructions

### Requirements

- Python 3.10 or later (developed and tested with Python 3.14).
- A display (X11/Wayland/Windows/macOS). For headless runs, set
  `SDL_VIDEODRIVER=dummy`.

### Installation

```console
$ make install
```

This installs all dependencies from `requirements.txt`: the `pygame-ce`
graphical library, the assigned A-Maze-ing package (installed from the
provided wheel `mazegenerator-00001/mazegenerator-2.1.0-py3-none-any.whl`),
and the development tools (flake8, mypy, pytest, PyInstaller).

### Running the game

```console
$ python3 pac-man.py config.json
```

The program takes exactly one argument: a `.json` configuration file.
Any error (missing file, invalid JSON, missing or invalid values) is
reported with a clear message on the console and safe defaults are used —
the game never crashes and never shows a Python traceback.

### Controls

| Action            | Key(s)                              |
|-------------------|-------------------------------------|
| Move              | Arrow keys or WASD                  |
| Pause / Resume    | `P` or `Esc` (pause menu)           |
| Cheat menu        | `C`                                 |
| Menu navigation   | Arrows / WASD + `Enter`, or mouse   |

### Makefile targets

| Target         | Purpose                                              |
|----------------|------------------------------------------------------|
| `make install` | Install all dependencies                              |
| `make run`     | Launch the game (`python3 pac-man.py config.json`)    |
| `make debug`   | Launch the game under the `pdb` debugger              |
| `make clean`   | Remove caches and build artifacts                     |
| `make lint`    | `flake8 .` + `mypy .` with the mandatory flags        |
| `make lint-strict` | Same with `mypy . --strict` (optional)            |
| `make build`   | Build a standalone package with PyInstaller           |

## Configuration

The configuration file is JSON with comments: lines starting with `#` (or
`//`) are ignored, and inline comments outside of string literals are
stripped as well. Every key is optional — missing or invalid values are
clamped to safe defaults and reported on the console; unknown keys are
ignored.

| Key                          | Default             | Meaning                                                            |
|------------------------------|---------------------|--------------------------------------------------------------------|
| `highscore_filename`         | `"highscores.json"` | File where the top-10 highscores are saved (JSON).                 |
| `lives`                      | `3`                 | Lives at game start (clamped 1-9).                                 |
| `pacgum`                     | `42`                | Percentage (1-100) of corridor cells holding a pacgum.             |
| `points_per_pacgum`          | `10`                | Points for eating a pacgum.                                        |
| `points_per_super_pacgum`    | `50`                | Points for eating a super-pacgum.                                  |
| `points_per_ghost`           | `200`               | Points for eating an edible ghost.                                 |
| `seed`                       | `42`                | Fixed seed of the first level (later levels are random).           |
| `level_max_time`             | `90`                | Time limit per level in seconds (10-600).                          |
| `super_pacgum_duration`      | `8`                 | Seconds ghosts stay edible after a super-pacgum (1-30).            |
| `ghost_respawn_time`         | `8`                 | Seconds an eaten ghost takes to walk back to its corner (1-30).    |
| `levels`                     | 10 default levels   | Array of `{"width": W, "height": H}` level definitions (15-60).    |

Example:

```json
{
  # This file uses JSON with comments.
  "lives": 3,
  "pacgum": 42,
  "seed": 42,
  "level_max_time": 90,
  "levels": [
    { "width": 15, "height": 15 },
    { "width": 21, "height": 19 }
  ]
}
```

The shipped `config.json` defines 10 levels whose maze sizes grow from
15x15 to 31x19.

## Highscore

Highscores are persisted in a JSON file on disk (path configurable through
the `highscore_filename` key). The file is loaded when the game starts and
saved when a game ends and a name is entered. The table keeps the **top 10
entries**, each storing a player name and a non-negative integer score,
sorted descending.

- Names are limited to **10 characters, alphanumeric and spaces only**.
- Scores must be **non-negative integers**.
- The loader is robust: a missing or corrupted file, or invalid entries
  inside a valid file, are reported with a warning and simply skipped.
- The top-10 table is displayed in the main menu ("View Highscores").

**Why this design?** A plain JSON file was chosen because it is human
readable, trivially portable between platforms, and matches the "stored on
disk in the project" requirement with zero extra dependencies. Loading and
saving are isolated in a single module (`src/highscores.py`) with
validation at the boundaries, so the game itself never has to worry about
corrupt data.

## Maze Generation

Mazes are generated by the **A-Maze-ing** package assigned to this project
(`mazegenerator`, provided as the wheel
`mazegenerator-00001/mazegenerator-2.1.0-py3-none-any.whl`). The package
is used **exactly as shipped — it is never modified**. The adapter in
`src/maze_loader.py` adapts to *its* interface, not the other way around:

```python
from mazegenerator import MazeGenerator

generator = MazeGenerator(size=(width, height), perfect=False, seed=42)
grid = generator.maze  # grid[y][x], wall bits: N=1, E=2, S=4, W=8
```

- `perfect` is always set to `False`, which makes the A-Maze-ing package
  braid the maze (remove dead ends) and produce the loops and multiple
  paths Pac-Man needs.
- The **first level** uses the fixed seed from the configuration; every
  **subsequent level is randomly generated** (`seed=0`).
- The wall encoding is interpreted per cell: a bit set means the wall
  exists, and a cell with value 15 (all walls) is a solid pillar that
  cannot be entered.
- If the generator fails, the adapter retries with a random seed and, if
  the package keeps failing, raises a clean `MazeError` which the entry
  point reports without a traceback.

## Implementation

The implementation is fully object-oriented and split into focused modules:

- `src/config.py` — JSON-with-comments configuration loading, clamping and
  safe defaults.
- `src/maze_loader.py` — adapter for the A-Maze-ing package and wall
  helpers (movement checks, nearest walkable cell).
- `src/highscores.py` — persistent top-10 highscore table.
- `src/ai.py` — ghost pathfinding: BFS distance maps, greedy chase/flee
  step selection with random tie-breaking.
- `src/entities.py` — `Player`, `Ghost` and `CheatState`.
- `src/game.py` — the pure game logic (no graphics): levels, movement,
  scoring, ghost modes, time limit, game progression and events.
- `src/renderer.py` — pygame rendering of the maze, entities and HUD.
- `src/ui.py` — pygame menus and screens (main menu, highscores,
  instructions, pause, cheat menu, name entry).
- `src/main.py` — the application: pygame event loop and screen state
  machine.

Key gameplay details:

- Movement is grid-based with smoothed interpolation; the player can move
  in the 4 directions through corridors only.
- Super-pacgums sit in the 4 corners; pacgums fill a configurable
  percentage of the other corridors; the player spawns in the middle.
- Ghosts chase the player (distance-based), run away when edible, and walk
  back to their corner after being eaten.
- The player starts with 3 lives and respawns in the middle after losing
  one. Running out of time costs a life and restarts the level.
- The score only ever increases (pacgums +10, super-pacgums +50, edible
  ghosts +200 by default).
- Cheat mode (`C` in game): invincibility, skip level, ghost freeze, extra
  life and increased speed — one key each, so every feature of the game
  can be demonstrated quickly during review.
- Constants such as movement speeds and durations live at the top of the
  modules where they are used.

## General Software Architecture

```
pac-man.py                      entry point (argument validation, clean errors)
   |
   v
src/main.py (PacmanApp)         pygame loop, screen state machine, input
   |          |          |
   v          v          v
src/ui.py   src/renderer.py   src/game.py (PacmanGame)
menus &     drawing of the    pure game logic: levels, entities,
screens     game view, HUD    scoring, progression, events
                                |
                                +-- src/entities.py (Player, Ghost, Cheats)
                                +-- src/ai.py (BFS chase/flee)
                                +-- src/maze_loader.py (A-Maze-ing adapter)
                                +-- src/highscores.py (top-10 table)
                                +-- src/config.py (validated configuration)
```

The application layer (`PacmanApp`) owns the window and input; the game
layer (`PacmanGame`) owns the rules and never touches pygame; the
rendering layer only reads game state. This separation keeps the game
logic fully unit-testable without a display.

The game is playable entirely with the keyboard (and the mouse for the
menus). Screens: main menu (Start Game / View Highscores / Instructions /
Exit), game view with an always-visible HUD (score, lives, level, time),
pause menu (Resume / Return to Main Menu), cheat menu, game-over and
victory screens with name entry.

## Project Management

The activity was driven with a structured approach; all management
documents (timeline, progress tracking, project and risk analysis, team
organization, acceptance test plan, blocking points) are stored in the
dedicated [`project_management/`](project_management/) directory.

## Resources

Classic references:

- Pac-Man (Namco, 1980) — original gameplay, ghost AI behaviors.
- MiniLibX documentation — the reference 2D graphical library this
  activity builds upon ("MLX or similar").
- pygame documentation — https://www.pygame.org/docs/
- PEP 257 (docstrings), flake8 and mypy documentation for code quality.
- The A-Maze-ing `mazegenerator` package documentation (see the wheel's
  METADATA and the module docstring in `mazegenerator/mazegenerator.py`).

### How AI was used

AI was used for the following tasks:

- Drafting the initial project structure and the configuration loader.
- Implementing the ghost pathfinding (BFS) and the game state machine.
- Writing the unit tests and the packaging configuration.
- Reviewing the code for edge cases (e.g., sealed maze cells, level
  transitions during a walk, pygame headless testing).

All generated code was reviewed, tested (flake8, mypy, pytest) and adapted
to the project requirements. The maze generation logic itself comes
exclusively from the assigned A-Maze-ing package and was not modified.

## Packaging and Deployment

The repository contains the full source and the packaging spec at the root
(`pacman.spec`, PyInstaller). See [`packaging/`](packaging/) for the build
instructions and the Itch.io deployment guide.