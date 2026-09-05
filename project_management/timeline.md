# Project Timeline

The activity was planned with the following milestones. Duration estimates
are in working sessions (each session ≈ half a day).

| # | Milestone                          | Planned | Actual | Status |
|---|------------------------------------|---------|--------|--------|
| 1 | Read the subject, extract requirements | Day 1  | Day 1  | Done |
| 2 | Inspect the A-Maze-ing package interface | Day 1 | Day 1 | Done |
| 3 | Project skeleton (Makefile, gitignore, requirements) | Day 1 | Day 1 | Done |
| 4 | Configuration loader (JSON with comments, clamping) | Day 2 | Day 2 | Done |
| 5 | Maze adapter + wall helpers          | Day 2   | Day 2  | Done |
| 6 | Highscore system                    | Day 2   | Day 2  | Done |
| 7 | Core game logic (entities, levels, scoring) | Day 3 | Day 3 | Done |
| 8 | Ghost AI (chase/flee, respawn)      | Day 3   | Day 3  | Done |
| 9 | Rendering and UI (menu, HUD, screens) | Day 4 | Day 4 | Done |
| 10| Cheat mode                          | Day 4   | Day 4  | Done |
| 11| Tests + lint (flake8, mypy, pytest) | Day 5  | Day 5  | Done |
| 12| README, packaging spec, deployment docs | Day 5 | Day 5 | Done |
| 13| Final audit against the subject     | Day 5   | Day 5  | Done |

Gantt-style overview:

```
Day 1  |████ requirements + skeleton + package inspection|
Day 2  |████ config + maze adapter + highscores          |
Day 3  |████████ game logic + ghost AI                   |
Day 4  |████████ rendering + UI + cheat mode             |
Day 5  |████ tests + lint + docs + packaging + audit     |
```