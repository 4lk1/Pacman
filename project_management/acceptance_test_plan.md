# Acceptance Test Plan

## Test strategy

- **Unit tests** (run during development): configuration, highscores, maze
  adapter, game logic, and a headless end-to-end application run. These
  development-only tests are intentionally excluded from the delivery
  package.
- **Static checks**: `flake8 .` (clean) and `mypy .` with the mandatory
  flags (clean).
- **Manual/headless runs**: the full game loop was exercised through the
  pygame dummy video driver: menu → start → play → win (cheat skip) →
  name entry → back to menu; broken configs were run through the CLI.

## Features tested (all pass)

| Feature                       | Validation                                                     |
|-------------------------------|------------------------------------------------------------------|
| JSON comments (# and //)      | Development unit tests                                           |
| Config defaults & clamping    | Development unit tests                                           |
| Unknown keys ignored          | Development unit tests                                           |
| Missing/broken config file    | Development unit tests and CLI runs                              |
| Maze generation via package   | Development unit tests                                           |
| Wall/movement encoding        | Development unit tests                                           |
| Highscore validation & top 10 | Development unit tests                                           |
| Corrupted highscore file      | Development unit tests                                           |
| Player movement & wall blocking | Development unit tests                                         |
| Pacgum/super-pacgum scoring   | Development unit tests                                           |
| Ghost chase/flee/eaten/respawn| Development unit tests                                           |
| Lives, respawn, game over     | Development unit tests                                           |
| Timeout restart               | Development unit tests                                           |
| Level progression & victory   | Development unit tests                                           |
| All cheat features            | Development unit tests                                           |
| Full game loop (headless)     | Manual/headless validation                                        |

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