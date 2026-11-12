"""Read-only view of ~/.ssh/known_hosts. Editing is out of v1."""

from dataclasses import dataclass
from pathlib import Path

HASHED = "(hashed host)"


@dataclass(frozen=True)
class KnownHost:
    hosts: str
    key_type: str
    marker: str = ""


def default_known_hosts() -> Path:
    return Path.home() / ".ssh" / "known_hosts"


def read_known_hosts(path: Path) -> list[KnownHost]:
    """Entries from a known_hosts file. Hashed names are shown as a placeholder."""
    if not path.exists():
        return []
    entries: list[KnownHost] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        marker = ""
        if parts[0].startswith("@"):
            marker = parts.pop(0)
        if len(parts) < 3:
            continue
        names, key_type = parts[0], parts[1]
        if names.startswith("|1|"):
            names = HASHED
        entries.append(KnownHost(hosts=names.replace(",", ", "), key_type=key_type, marker=marker))
    return entries
