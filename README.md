# SSHinator

A terminal UI for browsing, connecting to, and editing the hosts in your `~/.ssh/config`. Built with Python and [Textual](https://textual.textualize.io/).

SSHinator edits your real config file, so every save shows a diff preview first, and a timestamped backup is kept. The first run asks you to accept a one-time warning before it opens.

Supported: macOS. Linux is a stated requirement and is not yet tested.

## Install

Requires Python 3.11 or newer.

```bash
git clone <this repo> sshinator
cd sshinator
bash scripts/install-pipx.sh
```

The script installs [pipx](https://pipx.pypa.io/) with Homebrew if it is missing, then installs `sshinator` as a command on your PATH. Run it again to upgrade. To pick up local changes, use `scripts/upgrade-sshinator.sh`.

## Use

```bash
sshinator                     # open your ~/.ssh/config
sshinator --config PATH       # open a copy of a config instead
sshinator --reset             # show the first-run warning again
```

| Key | Action |
|---|---|
| ↑ / ↓ | Move the highlight |
| ENTER | Connect to the highlighted host |
| SPACE | Expand a group, or a host's details |
| e | Edit the host |
| / | Search by alias or HostName |
| ESC | Clear the search, or quit when no search is open |
| q | Quit from the host list |
| Ctrl+R | Reload the config |

Hosts are listed as `HostName (alias)`. A `# [group: NAME]` line in your config groups every host below it, until the next group line. Hosts above the first group line are listed under Ungrouped.

## Develop

```bash
python3 -m venv ~/.venvs/sshinator-test
~/.venvs/sshinator-test/bin/pip install -e . pytest pytest-asyncio
~/.venvs/sshinator-test/bin/python -m pytest -q tests
```

The tests use temporary configs and never touch your real `~/.ssh/config`.

## Project notes

Design notes, decisions, and plans live in [`docs/`](docs/), an Obsidian vault. To fork this project and continue it, start with [`docs/00 - Start Here/How to Use This Vault.md`](docs/00%20-%20Start%20Here/How%20to%20Use%20This%20Vault.md).

## License

MIT. See [LICENSE](LICENSE).
