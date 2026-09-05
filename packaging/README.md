# Packaging

This directory contains everything needed to turn the Pac-Man source into a
standalone game package that can be installed and launched from a public
gaming platform (e.g. Itch.io) as a free, unlisted/private build.

The packaging spec lives at the **repository root** (`pacman.spec`), as
required, together with the full source code.

## Building the standalone package

Requirements: `pyinstaller` (installed by `make install`).

```console
$ make build
# or: python3 -m PyInstaller pacman.spec --noconfirm
```

Output:

- `dist/pacman/` — a folder with the executable `pacman`, Python, the
  pygame library, the A-Maze-ing `mazegenerator` package (bundled in the
  PYZ archive) and `packaging/INSTRUCTIONS.txt`. With PyInstaller 6.x the
  instructions file ends up at
  `dist/pacman/_internal/packaging/INSTRUCTIONS.txt`.
- `build/pacman/` — intermediate build artifacts (safe to delete with
  `make clean`).

To produce a package for another platform, run the build on that platform
(PyInstaller does not cross-compile): build on Windows for Windows, on
Linux for Linux, on macOS for macOS.

The packaged game is fully functional and needs no Python installation.

> **Tip:** if PyInstaller reports ``The 'typing' package is an obsolete
> backport ... incompatible`` (a broken pre-installed package in some
> environments), build inside a virtual environment instead:
>
> ```console
> $ python3 -m venv .venv
> $ .venv/bin/pip install -r requirements.txt
> $ .venv/bin/python -m PyInstaller pacman.spec --noconfirm
> ```

## Deploying to Itch.io (free, unlisted build)

1. Create an account on https://itch.io and download the `butler`
   command-line tool: https://itch.io/docs/butler/
2. Create a new project on itch.io (type: game, price: free, visibility:
   unlisted or draft while testing).
3. Push the packaged folder:

   ```console
   $ butler push dist/pacman your_username/your_game:windows-linux
   ```

   Adjust the channel name to the platform(s) you built for
   (`windows`, `linux`, `mac`, or a combined name).
4. Upload at least one screenshot or cover image in the project's edit
   page (Itch.io requires media for the game page).
5. Publish the build. The game page then links directly to the package;
   players download it, unzip it and launch `pacman` (or `pacman.exe`).
6. Optional: to ship a config file with the game, keep `config.json`
   next to the executable (the game also runs with defaults if the file
   is missing or broken).

`deploy_itch.sh` automates step 3 for Linux builds:

```console
$ ./packaging/deploy_itch.sh your_username/your_game
```

## Notes

- The game logs warnings to the console (e.g. clamped config values), so
  the packaged executable intentionally keeps a console window.
- `highscores.json` is created next to the game when the first score is
  saved; if the folder is read-only the game logs a warning and continues
  (the highscore simply is not persisted).
- `pacman.spec` collects the `mazegenerator` package and its submodules
  via `collect_submodules`, so the bundled game generates mazes with the
  assigned A-Maze-ing package just like the source version.