#!/usr/bin/env bash
# Deploy the packaged Pac-Man build to Itch.io with butler.
#
# Usage:  ./packaging/deploy_itch.sh your_username/your_game
#
# Requires:
#   - a built package in dist/pacman (run `make build` first)
#   - the butler CLI on PATH (https://itch.io/docs/butler/)
#
# The build is pushed as a free, unlisted/private build: set the
# visibility on the Itch.io project page.

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 your_username/your_game" >&2
    exit 1
fi

PROJECT="$1"
PACKAGE="dist/pacman"

if [ ! -d "$PACKAGE" ]; then
    echo "Error: '$PACKAGE' not found. Run 'make build' first." >&2
    exit 1
fi

echo "Pushing $PACKAGE to $PROJECT (channel: linux)..."
butler push "$PACKAGE" "$PROJECT:linux"

echo
echo "Done. Open your Itch.io project page, add a cover image and"
echo "publish the build. Remember: keep it free and unlisted/private."