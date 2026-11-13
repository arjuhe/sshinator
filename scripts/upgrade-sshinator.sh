#!/usr/bin/env bash
# Upgrade only SSHinator to the code in this project folder.
#
# SSHinator is installed from this local folder, so the upgrade rebuilds it
# from the current source. Run it from anywhere:
#
#   bash <project>/scripts/upgrade-sshinator.sh

# Stop at the first error, and treat unset variables as errors.
set -euo pipefail

# The folder that holds pyproject.toml, derived from this script's location.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Step 1: make sure pipx is installed.
if ! command -v pipx >/dev/null 2>&1; then
  echo "pipx not found. Install it first with: brew install pipx" >&2
  exit 1
fi

# Step 2: reinstall from the project folder. --force replaces the current
# install, so this picks up any code changes.
pipx install --force "$PROJECT_DIR"

echo "Upgraded: $(pipx list --short | grep '^sshinator ' || echo 'sshinator')"
