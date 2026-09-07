# Risk Analysis

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | A-Maze-ing package interface changes before review | Low | High | Adapter isolates the package (`src/maze_loader.py`); only that module touches `mazegenerator`. |
| 2 | Maze generator fails or returns invalid data | Low | High | Retry with random seed, validate the grid, clean `MazeError` -> clear message, no traceback. |
| 3 | Reviewer breaks the config file during defense | Medium | Medium | Every key optional; invalid values clamped with warnings; missing file -> defaults; game still runs. |
| 4 | Highscore file corrupted or missing | Medium | Low | Robust loader drops invalid entries, starts empty, logs warnings. |
| 5 | Headless environment during development | High | Medium | SDL dummy driver; game logic fully decoupled from pygame and unit-tested. |
| 6 | No display/fonts on the packaged target | Low | Medium | pygame's bundled default font (`Font(None, ...)`), no external assets. |
| 7 | Packaged build misses the mazegenerator package | Low | High | `collect_submodules("mazegenerator")` in the spec; smoke-tested build. |
| 8 | Player spawn lands on a wall (42 pattern) | Medium | Low | `nearest_walkable` fallback places the player/ghosts/pellets on the closest walkable cell. |
| 9 | Timeout/level-transition edge cases | Medium | Low | Covered by unit tests (timeout restart, last-pacgum level completion). |
| 10 | Unhandled pygame error at startup (no video) | Medium | Medium | Top-level exception handler prints a clean message; never a traceback. |

Overall exposure: low. The highest-impact risks (1, 7) are structural:
both are contained by the adapter pattern and the packaging spec, and both
are re-verified at review time (the package is re-installed from the
provided wheel, the package is rebuilt with `make build`).
