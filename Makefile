# Pac-Man — automation Makefile
#
# Targets:
#   install      Install all dependencies (pygame-ce, the A-Maze-ing
#                wheel, lint tools, PyInstaller).
#   run          Launch the game: python3 pac-man.py config.json
#   debug        Launch the game under the pdb debugger.
#   clean        Remove caches, build and dist directories.
#   lint         flake8 + mypy with the mandatory flags.
#   lint-strict  flake8 + mypy --strict (optional, enhanced checking).
#   build        Build a standalone package with PyInstaller.

PYTHON ?= python3
CONFIG ?= config.json

.PHONY: install run debug clean lint lint-strict build

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) pac-man.py $(CONFIG)

debug:
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	rm -rf build dist
	rm -rf .venv

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

build:
	$(PYTHON) -m PyInstaller pacman.spec --noconfirm