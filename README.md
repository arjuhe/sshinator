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
sshinator                                # open your ~/.ssh/config in safe mode
sshinator --config PATH                  # open a copy of a config instead
sshinator --reset                        # show the first-run warning again
sshinator --accept                       # accept the one-time warning and exit
sshinator --safe                         # start in safe mode
sshinator --dont-blame-doofenshmirtz     # advanced: unsafe mode
```

- `--accept` writes the one-time gate acceptance and exits. It cannot be combined with any other option.
- `--safe` starts in safe mode and deletes the unsafe acceptance file if it exists, so unsafe must be asked for again. It cannot be combined with `--dont-blame-doofenshmirtz`, `--accept`, or `--reset`.
- `--dont-blame-doofenshmirtz` is the advanced unsafe mode. It needs the first-run warning to be accepted first, and it always shows the unsafe box. Accepting makes unsafe the default for later launches, until `--safe` is used. Declining keeps safe mode for that session.

The default is safe mode. Safe mode shows a shadow-backup box before each save. Unsafe mode skips that box. A backup is still made.

SSHinator has two tabs: Hosts (from your `~/.ssh/config`) and Known hosts (from `~/.ssh/known_hosts`, read-only). The left and right arrows switch tabs.

| Key | Action |
|---|---|
| ← / → | Switch tabs |
| ↑ / ↓ | Move the highlight |
| ENTER | Connect to the highlighted host |
| SPACE | Expand a group, or a host's details (Hosts tab) |
| e | Edit the host (Hosts tab) |
| / | Search by alias or HostName (Hosts tab) |
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
