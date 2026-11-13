#!/usr/bin/env bash
# Upgrade every app pipx manages, including SSHinator.
#
# Run it from anywhere:
#
#   bash <project>/scripts/upgrade-all.sh
#
# To upgrade only SSHinator from this project's code, use upgrade-sshinator.sh.

# Stop at the first error, and treat unset variables as errors.
set -euo pipefail

# Step 1: make sure pipx is installed.
if ! command -v pipx >/dev/null 2>&1; then
  echo "pipx not found. Install it first with: brew install pipx" >&2
  exit 1
fi

# Step 2: upgrade all pipx-managed apps.
pipx upgrade-all
