# Project Analysis and Choices

## Requirements extraction

The subject (PDF) was read entirely and its requirements were extracted
into a checklist before any implementation:

- Python 3.10+, flake8, mypy (typed code, no errors), docstrings.
- Makefile with `install`, `run`, `debug`, `clean`, `lint`
  (`lint-strict` optional).
- `python3 pac-man.py config.json`: exactly one `.json` argument, no
  traceback ever.
- JSON configuration with `#` comments, safe defaults, clamping, unknown
  keys ignored.
- Level generation **only** through the assigned A-Maze-ing package
  (`perfect=False`), adapter adapts to its interface.
- Persistent top-10 highscore system (JSON file), name validation
  (<= 10 chars, alphanumeric + spaces), non-negative scores.
- Game: >= 10 levels, fixed seed on level 1, random afterwards; pacgums
  in corridors, super-pacgums in the 4 corners, 4 ghosts, player in the
  middle; 3 lives; time limit; pause; win/lose -> name entry -> main menu.
- Cheat mode for review.
- Polished UI: main menu (4 items), HUD (score/lives/level/time), pause
  menu (2 items), game-over and victory screens.
- Packaging script/spec at the repo root; in-package instructions.
- Project management documents in a dedicated directory.
- README.md with the mandated first line and sections.

## Technical choices

| Decision | Choice | Rationale |
|---|---|---|
| Graphical library | pygame-ce ("MLX or similar") | Pygame primitives map 1:1 to MLX calls; it is the standard simple 2D Python library. |
| Game logic / rendering split | `src/game.py` is pygame-free | The rules are unit-testable headless; rendering only reads state. |
| Movement model | Grid-based cells with interpolation | Simple, deterministic, matches the wall-bit encoding, easy to test. |
| `pacgum` config key | Percentage of corridors (default 42) | Scales with maze size; documented in README. |
| Ghost AI | Greedy BFS distance (chase) / farthest (flee) | Explicitly allowed by the subject (distance-based, random, etc.). |
| Timeout behavior | Costs a life + level restart | One of the options the subject suggests; keeps pressure without ending the run instantly. |
| Highscore storage | Plain JSON file (top 10) | Human-readable, zero dependencies, robust loader. |
| Missing/invalid config file | Log warning + continue with defaults | "Handle cleanly and continue" - the game never crashes. |
| Packaging | PyInstaller spec at repo root | Standalone folder deployable to Itch.io (free, unlisted build). |

## Alternatives considered and rejected

- **Writing our own maze generator** - explicitly prohibited by the
  subject; the A-Maze-ing package is used as-is.
- **A full game engine (e.g. arcade/pyglet/panda3d)** - not "MLX or
  similar"; pygame primitives map 1:1 to MLX calls.
- **SQLite or network storage for highscores** - overkill; a JSON file
  satisfies the requirement with no dependencies.
- **Fixed pacgum count** - a fixed count would look sparse on large
  mazes; a percentage adapts to any level size.
