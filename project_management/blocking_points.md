# Blocking Points and Conflicts

## Blocking points

| # | Blocking point                                          | Resolution                                                        |
|---|---------------------------------------------------------|-------------------------------------------------------------------|
| 1 | The A-Maze-ing package interface was undocumented in the subject (wall encoding, constructor). | The provided wheel was unpacked and its source read to learn the exact interface; the adapter was written against the real code. |
| 2 | No display available in the development environment.     | SDL dummy video driver + a strict separation between game logic and pygame, making everything testable headless. |
| 3 | Packaging for a public platform requires an account/credentials that a development environment cannot provide. | The packaging spec, build commands and a butler deployment script are provided and tested as far as possible locally; the actual upload is a documented 3-step manual action for the owner's Itch.io account. |
| 4 | Python 3.14 in the environment vs "3.10 or later" requirement. | 3.14 satisfies "3.10 or later"; code avoids 3.12+ only syntax and is mypy/flake8 clean. |

## Conflicts

- **`pacgum: 42` interpretation** — the subject lists `pacgum: 42` as a
  suggested key without units. Interpreted as a percentage of corridor
  cells (documented in the README and config comments); this was the
  interpretation that stays valid for every maze size.
- **Timeout behavior** — the subject explicitly leaves the choice open
  ("you can decide"); chose "costs a life + restarts the level", the
  option that keeps the game progressing without ending the run.

## Status

No open blocking points remain. All decisions were recorded in
[`analysis.md`](analysis.md) and are defensible directly from the subject
text.