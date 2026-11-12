"""Read and write ~/.ssh/config without losing anything the user wrote by hand.

The file is split into blocks. Each block keeps its leading lines (comments,
blank lines, group markers), its ``Host`` header, its body, and its trailing
lines. Rendering the blocks back out reproduces the original text exactly, so
an untouched block is always written back verbatim.
"""

import difflib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# Options the edit form manages. Anything else in a host block is kept as-is.
MANAGED = {
    "hostname": "HostName",
    "user": "User",
    "port": "Port",
    "identityfile": "IdentityFile",
    "proxyjump": "ProxyJump",
    "stricthostkeychecking": "StrictHostKeyChecking",
}

GROUP_RE = re.compile(r"^#+\s*\[group:\s*(.+?)\s*\]\s*$", re.IGNORECASE)
HEADER_RE = re.compile(r"^\s*(host|match)(\s|$)", re.IGNORECASE)
OPTION_RE = re.compile(r"^\s*([A-Za-z]+)(?:\s*=\s*|\s+)(.*?)\s*$")


@dataclass
class Block:
    pre: list[str] = field(default_factory=list)
    header: str | None = None
    body: list[str] = field(default_factory=list)
    post: list[str] = field(default_factory=list)

    def render(self) -> str:
        header = [self.header] if self.header is not None else []
        return "".join(self.pre + header + self.body + self.post)

    @property
    def keyword(self) -> str:
        return self.header.split()[0].lower() if self.header else ""

    @property
    def aliases(self) -> list[str]:
        return self.header.split()[1:] if self.header else []

    @property
    def group(self) -> str | None:
        name = None
        for line in self.pre:
            match = GROUP_RE.match(line.rstrip("\r\n"))
            if match:
                name = match.group(1)
        return name

    def options(self) -> dict[str, str]:
        """Return the first value of each managed option, keyed by canonical name."""
        values: dict[str, str] = {}
        for line in self.body:
            match = OPTION_RE.match(line.rstrip("\r\n"))
            if not match:
                continue
            key = MANAGED.get(match.group(1).lower())
            if key and key not in values:
                values[key] = match.group(2)
        return values


@dataclass
class HostEntry:
    """A concrete host the list shows: a block with a plain (non-wildcard) alias."""

    block: Block
    alias: str
    hostname: str
    group: str | None


@dataclass
class SshConfig:
    blocks: list[Block]

    @classmethod
    def parse(cls, text: str) -> "SshConfig":
        blocks: list[Block] = []
        pending: list[str] = []
        current: Block | None = None
        for line in text.splitlines(keepends=True):
            if HEADER_RE.match(line):
                if current is not None:
                    _split_post(current)
                    # Comments after a block usually describe the next one, so
                    # they move into its leading lines (group markers included).
                    pending = current.post
                    current.post = []
                current = Block(pre=pending, header=line)
                blocks.append(current)
                pending = []
            elif current is None:
                pending.append(line)
            else:
                current.body.append(line)
        if current is not None:
            _split_post(current)
        else:
            # No header at all: keep the whole file as one headerless block.
            blocks.append(Block(pre=pending))
        return cls(blocks)

    def render(self) -> str:
        return "".join(block.render() for block in self.blocks)

    def hosts(self) -> list[HostEntry]:
        """Concrete hosts only. Wildcard, negated, and ``Match`` blocks are skipped."""
        entries: list[HostEntry] = []
        group: str | None = None
        for block in self.blocks:
            # A group marker covers every host below it, up to the next marker.
            group = block.group or group
            if block.keyword != "host" or not block.aliases:
                continue
            if any(_is_pattern(alias) for alias in block.aliases):
                continue
            options = block.options()
            alias = " ".join(block.aliases)
            entries.append(
                HostEntry(
                    block=block,
                    alias=alias,
                    hostname=options.get("HostName", block.aliases[0]),
                    group=group,
                )
            )
        return entries

    def find(self, block: Block) -> int:
        for index, candidate in enumerate(self.blocks):
            if candidate is block:
                return index
        raise ValueError("block is not part of this config")


def _is_pattern(alias: str) -> bool:
    return alias.startswith("!") or "*" in alias or "?" in alias


def _split_post(block: Block) -> None:
    """Move trailing blank and comment lines out of the body into ``post``."""
    while block.body:
        stripped = block.body[-1].strip()
        if stripped and not stripped.startswith("#"):
            break
        block.post.insert(0, block.body.pop())


def build_block(block: Block, alias: str, values: dict[str, str]) -> Block:
    """Return a copy of ``block`` with the alias and managed options replaced.

    Unmanaged lines are kept. Managed options with an empty value are removed.
    """
    header = block.header
    if header is not None:
        keyword = header.split()[0]
        ending = "\n" if header.endswith("\n") else ""
        header = f"{keyword} {alias}{ending}"

    indent = "  "
    for line in block.body:
        match = OPTION_RE.match(line.rstrip("\r\n"))
        if match and match.group(1).lower() in MANAGED:
            indent = line[: len(line) - len(line.lstrip())] or "  "
            break

    body: list[str] = []
    seen: set[str] = set()
    for line in block.body:
        match = OPTION_RE.match(line.rstrip("\r\n"))
        key = MANAGED.get(match.group(1).lower()) if match else None
        if key is None:
            body.append(line)
            continue
        if key in seen:
            continue  # duplicate managed option: the first one wins, as in ssh
        seen.add(key)
        value = values.get(key, "")
        if value:
            body.append(f"{indent}{key} {value}\n")
    for key, value in values.items():
        if key not in seen and value:
            body.append(f"{indent}{key} {value}\n")

    return Block(pre=list(block.pre), header=header, body=body, post=list(block.post))


def unified_diff(old_text: str, new_text: str, name: str) -> str:
    return "".join(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"{name} (current)",
            tofile=f"{name} (new)",
        )
    )


def next_backup_path(backup_dir: Path) -> Path:
    """Name for a new backup: ``shadow_backup-YYYYMMDD-HHMMSS.bak``.

    If that name is taken (two saves in one second), wait for the next second.
    """
    import time
    from datetime import datetime

    while True:
        path = backup_dir / f"shadow_backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
        if not path.exists():
            return path
        time.sleep(0.2)


def backup(path: Path, backup_dir: Path, keep: int = 20, target: Path | None = None) -> Path:
    """Copy ``path`` into ``backup_dir`` (as ``target`` if given) and prune old copies."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.chmod(0o700)
    target = target or next_backup_path(backup_dir)
    # Created as 0600 directly, so the umask cannot make it more readable.
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(path.read_bytes())
    copies = sorted(backup_dir.glob("shadow_backup-*.bak"))
    for old in copies[:-keep]:
        old.unlink()
    for kept in copies[-keep:]:
        kept.chmod(0o600)
    return target


def write_atomic(path: Path, text: str) -> None:
    """Replace ``path`` in one step, keeping its permissions."""
    import os
    import tempfile

    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".config-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
