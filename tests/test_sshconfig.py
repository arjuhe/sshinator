import stat
from sshinator import sshconfig
from sshinator.sshconfig import SshConfig, build_block

# Same shape as a real hand-written config: a global block, a comment-marked
# group, commented-out hosts, a section banner, and an unmanaged option.
SAMPLE = """\
Host *
  ForwardAgent yes
  ServerAliveInterval 30

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_arjuhe
  IdentitiesOnly yes
  UseKeychain yes
  AddKeysToAgent yes


### .LOCAL ( EXAMPLE LAB ) ####
# Host stormtrooper
#   hostname stormtrooper.local
# Host deej
#   hostname deej.local
# [group: lab]
Host example-mbp example2
  HostName example-mbp.local
  user exampleuser
Host web-1
  HostName 10.0.0.12
  Port 2222
  # keep this comment
  ProxyJump bastion
#############################
"""


def test_round_trip_is_lossless():
    assert SshConfig.parse(SAMPLE).render() == SAMPLE


def test_lists_only_concrete_hosts():
    aliases = [entry.alias for entry in SshConfig.parse(SAMPLE).hosts()]
    assert aliases == ["github.com", "example-mbp example2", "web-1"]


def test_group_marker_covers_hosts_until_the_next_marker():
    entries = {e.alias: e for e in SshConfig.parse(SAMPLE).hosts()}
    assert entries["example-mbp example2"].group == "lab"
    assert entries["web-1"].group == "lab"
    assert entries["github.com"].group is None


def test_a_new_marker_starts_a_new_group():
    text = (
        "Host before\n  HostName before.example\n"
        "# [group: one]\nHost a\n  HostName a.example\n"
        "# [group: two]\nHost b\n  HostName b.example\n"
    )
    groups = {e.alias: e.group for e in SshConfig.parse(text).hosts()}
    assert groups == {"before": None, "a": "one", "b": "two"}


def test_group_marker_accepts_banner_style_from_real_config():
    text = (
        "### [Group: EXAMPLE LAB (*.LOCAL)] \n"
        "# Host stormtrooper\n"
        "Host example-mbp example2\n"
        "  HostName example-mbp.local\n"
    )
    entries = SshConfig.parse(text).hosts()
    assert entries[0].group == "EXAMPLE LAB (*.LOCAL)"


def test_hostname_defaults_to_alias_and_reads_options():
    entries = {e.alias: e for e in SshConfig.parse(SAMPLE).hosts()}
    assert entries["github.com"].hostname == "github.com"
    assert entries["example-mbp example2"].hostname == "example-mbp.local"
    assert entries["example-mbp example2"].block.options()["User"] == "exampleuser"


def test_edit_keeps_unmanaged_lines_and_comments():
    config = SshConfig.parse(SAMPLE)
    block = next(e for e in config.hosts() if e.alias == "web-1").block
    new = build_block(block, "web-1", {"HostName": "10.0.0.99", "Port": "2200", "ProxyJump": "bastion"})
    text = new.render()
    assert "HostName 10.0.0.99" in text
    assert "Port 2200" in text
    assert "# keep this comment" in text


def test_clearing_a_managed_option_removes_only_that_line():
    config = SshConfig.parse(SAMPLE)
    block = next(e for e in config.hosts() if e.alias == "web-1").block
    new = build_block(block, "web-1", {"HostName": "10.0.0.12", "Port": "", "ProxyJump": "bastion"})
    text = new.render()
    assert "Port" not in text
    assert "keep this comment" in text


def test_new_option_is_appended_with_the_block_indent():
    config = SshConfig.parse(SAMPLE)
    block = next(e for e in config.hosts() if e.alias == "github.com").block
    new = build_block(block, "github.com", {"HostName": "github.com", "StrictHostKeyChecking": "accept-new"})
    assert "  StrictHostKeyChecking accept-new\n" in new.body


def test_use_keychain_is_never_added():
    config = SshConfig.parse("Host plain\n  HostName plain.example\n")
    block = config.hosts()[0].block
    new = build_block(block, "plain", {"HostName": "plain.example", "User": "me"})
    assert "UseKeychain" not in new.render()


def test_rename_keeps_the_rest_of_the_file():
    config = SshConfig.parse(SAMPLE)
    old = next(e for e in config.hosts() if e.alias == "web-1").block
    new = build_block(old, "web-renamed", {"HostName": "10.0.0.12", "Port": "2222", "ProxyJump": "bastion"})
    rebuilt = SshConfig([new if b is old else b for b in config.blocks]).render()
    assert "Host web-renamed\n" in rebuilt
    assert "Host web-1\n" not in rebuilt
    assert "### .LOCAL ( EXAMPLE LAB )" in rebuilt


def test_backup_keeps_only_the_newest_20_and_leaves_old_names(tmp_path):
    config = tmp_path / "config"
    config.write_text("Host a\n", encoding="utf-8")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    for day in range(1, 25):
        (backup_dir / f"shadow_backup-202601{day:02d}-000000.bak").write_text("x")
    legacy = backup_dir / "config-20250101-000000-000000.bak"
    legacy.write_text("legacy")
    sshconfig.backup(config, backup_dir, keep=20)
    kept = sorted(backup_dir.glob("shadow_backup-*.bak"))
    assert len(kept) == 20
    assert not (backup_dir / "shadow_backup-20260101-000000.bak").exists()
    assert legacy.exists()


def test_backup_name_matches_template_and_waits_on_collision(tmp_path):
    import re

    config = tmp_path / "config"
    config.write_text("Host a\n", encoding="utf-8")
    backup_dir = tmp_path / "backups"
    first = sshconfig.backup(config, backup_dir)
    second = sshconfig.backup(config, backup_dir)
    assert first != second
    for path in (first, second):
        assert re.fullmatch(r"shadow_backup-\d{8}-\d{6}\.bak", path.name)


def test_write_atomic_keeps_mode(tmp_path):
    config = tmp_path / "config"
    config.write_text("Host a\n", encoding="utf-8")
    config.chmod(0o600)
    sshconfig.write_atomic(config, "Host b\n")
    assert config.read_text(encoding="utf-8") == "Host b\n"
    assert config.stat().st_mode & 0o777 == 0o600


def test_backups_are_private(tmp_path):
    config = tmp_path / "config"
    config.write_text(SAMPLE, encoding="utf-8")
    config.chmod(0o644)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    backup_dir.chmod(0o755)
    old = backup_dir / "shadow_backup-19990101-000000.bak"
    old.write_text("earlier copy", encoding="utf-8")
    old.chmod(0o644)

    target = sshconfig.backup(config, backup_dir)

    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE(old.stat().st_mode) == 0o600
    assert stat.S_IMODE(backup_dir.stat().st_mode) == 0o700


def test_backup_uses_the_planned_target(tmp_path):
    config = tmp_path / "config"
    config.write_text("Host a\n", encoding="utf-8")
    backup_dir = tmp_path / "backups"
    planned = sshconfig.next_backup_path(backup_dir)
    assert planned.parent == backup_dir
    assert sshconfig.backup(config, backup_dir, target=planned) == planned
    assert planned.read_text(encoding="utf-8") == "Host a\n"
