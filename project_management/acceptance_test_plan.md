# Acceptance Test Plan

## Test strategy

- **Unit tests** (pytest, `tests/`): configuration, highscores, maze
  adapter, game logic, and a headless end-to-end application run. All
  game tests run without a display.
- **Static checks**: `flake8 .` (clean) and `mypy .` with the mandatory
  flags (clean).
- **Manual/headless runs**: the full game loop was exercised through the
  pygame dummy video driver: menu → start → play → win (cheat skip) →
  name entry → back to menu; broken configs were run through the CLI.

## Features tested (all pass)

| Feature                       | Test(s)                                                          |
|-------------------------------|------------------------------------------------------------------|
| JSON comments (# and //)      | `tests/test_config.py`                                           |
| Config defaults & clamping    | `tests/test_config.py`                                           |
| Unknown keys ignored          | `tests/test_config.py`                                           |
| Missing/broken config file    | `tests/test_config.py`, CLI runs                                 |
| Maze generation via package   | `tests/test_maze_loader.py` (perfect=False, retry, error)        |
| Wall/movement encoding        | `tests/test_maze_loader.py`                                      |
| Highscore validation & top 10 | `tests/test_highscores.py`                                       |
| Corrupted highscore file      | `tests/test_highscores.py`                                       |
| Player movement & wall blocking | `tests/test_game.py`                                           |
| Pacgum/super-pacgum scoring   | `tests/test_game.py`                                             |
| Ghost chase/flee/eaten/respawn| `tests/test_game.py`                                             |
| Lives, respawn, game over     | `tests/test_game.py`                                             |
| Timeout restart               | `tests/test_game.py`                                             |
| Level progression & victory   | `tests/test_game.py`                                             |
| All cheat features            | `tests/test_game.py`, `tests/test_app.py`                        |
| Full game loop (headless)     | `tests/test_app.py`                                              |

## Bugs found and fixed during testing

| # | Bug                                                            | Fix                                                                |
|---|----------------------------------------------------------------|--------------------------------------------------------------------|
| 1 | `nearest_walkable` could not escape sealed (15) cells           | Switched to Manhattan-distance selection with deterministic ties.   |
| 2 | Game over check used `< 0` (allowed one extra death)            | Changed to `lives <= 0` after decrement.                            |
| 3 | Last-pacgum walk in tests didn't account for level transition   | Test helper now detects mid-walk level completion.                  |
| 4 | `pacgum: 0` produced an unwinnable level                       | Config clamps `pacgum` to a minimum of 1.                           |
| 5 | Config warning printed `levels[%d].width` literally             | Pre-format the key before logging.                                  |
| 6 | Headless tests: events posted before `pygame.init()`            | Create the app before posting events.                               |
| 7 | `event.unicode` missing on constructed test events              | Use `getattr(event, "unicode", "")`.                                |

All bugs above are covered by regression tests and were re-verified.