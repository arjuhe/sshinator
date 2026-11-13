#!/usr/bin/env bash
# Install SSHinator as a standalone `sshinator` command with pipx.
#
# pipx puts each app in its own isolated environment, so this does not touch
# the project's venv or your other Python tools. Run it from anywhere:
#
#   bash <project>/scripts/install-pipx.sh
#
# To update after changing the code, run it again. It reinstalls the app.

# Stop at the first error, and treat unset variables as errors.
set -euo pipefail

# The folder that holds pyproject.toml. Derived from this script's location,
# so the script works even if you move the whole project.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Step 1: make sure pipx is installed. Homebrew is the usual way on macOS.
if ! command -v pipx >/dev/null 2>&1; then
  echo "pipx not found. Installing it with Homebrew..."
  brew install pipx
fi

# Step 2: add pipx's bin folder (usually ~/.local/bin) to PATH, so the
# `sshinator` command can be found. This only edits your shell profile
# once; running it again changes nothing.
pipx ensurepath

# Step 3: install the project from its local folder. pipx builds a wheel,
# creates a private environment for it, and links the `sshinator` command.
# --force replaces an earlier install, so re-running this script upgrades it.
pipx install --force "$PROJECT_DIR"

# Step 4: check that the command is reachable. If this fails in a new
# terminal, open a new shell so the PATH change from step 2 takes effect.
if command -v sshinator >/dev/null 2>&1; then
  echo "Installed: $(command -v sshinator)"
  echo "Run it with: sshinator"
  echo "Or point it at a copy of your config: sshinator --config <path>"
else
  echo "Installed, but 'sshinator' is not on PATH in this shell."
  echo "Open a new terminal and run: sshinator"
fi
