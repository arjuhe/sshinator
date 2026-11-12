"""File locations used by SSHinator."""

import os
from pathlib import Path


def default_config() -> Path:
    return Path.home() / ".ssh" / "config"


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "sshinator"


def backup_dir() -> Path:
    return config_dir() / "sshinator-backups"


def accept_marker() -> Path:
    return config_dir() / "accepted"


def blame_marker() -> Path:
    return config_dir() / "doofenshmirtz-accepted"
