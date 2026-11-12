from textual.color import Color
import re

import pytest

from sshinator.app import BlameScreen, EditScreen, GateScreen, ShadowBackupScreen, SSHinator

from .test_sshconfig import SAMPLE


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config = tmp_path / "ssh" / "config"
    config.parent.mkdir()
    config.write_text(SAMPLE, encoding="utf-8")
    config.chmod(0o600)
    return config


def option_ids(app):
    from textual.widgets import OptionList

    option_list = app.screen.query_one("#hosts", OptionList)
    return [option_list.get_option_at_index(i).id for i in range(option_list.option_count)]


@pytest.mark.asyncio
async def test_gate_must_be_accepted_once(env, tmp_path):
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        assert isinstance(app.screen, GateScreen)
        await pilot.click("#accept")
        await pilot.pause()
        assert not isinstance(app.screen, GateScreen)
    assert (tmp_path / "xdg" / "sshinator" / "accepted").exists()


@pytest.mark.asyncio
async def test_gate_names_the_files_and_starts_on_quit(env, tmp_path):
    from textual.widgets import Button, Static

    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        text = str(app.screen.query_one("#dialog").query(Static).last().render())
        assert str(env) in text
        assert str(tmp_path / "xdg" / "sshinator" / "sshinator-backups") in text
        assert app.screen.focused.id == "decline"
        assert isinstance(app.screen.focused, Button)
        await pilot.press("left")
        assert app.screen.focused.id == "accept"
        await pilot.press("right")
        assert app.screen.focused.id == "decline"


@pytest.mark.asyncio
async def test_declining_the_gate_exits(env):
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.click("#decline")
        await pilot.pause()
    assert not app.is_running


@pytest.mark.asyncio
async def test_list_shows_groups_and_ungrouped(env, tmp_path, monkeypatch):
    marker_dir = tmp_path / "xdg" / "sshinator"
    marker_dir.mkdir(parents=True)
    (marker_dir / "accepted").write_text("accepted\n")
    app = SSHinator(env)
    async with app.run_test() as pilot:
        await pilot.pause()
        ids = option_ids(app)
        assert "group:lab" in ids
        assert "group:Ungrouped" in ids
        assert "host:web-1" in ids
        assert "host:example-mbp example2" in ids
        assert "host:*" not in ids


@pytest.mark.asyncio
async def test_search_filters_and_escape_clears(env, tmp_path):
    marker_dir = tmp_path / "xdg" / "sshinator"
    marker_dir.mkdir(parents=True)
    (marker_dir / "accepted").write_text("accepted\n")
    app = SSHinator(env)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("slash")
        await pilot.press(*"web")
        await pilot.pause()
        ids = option_ids(app)
        assert ids == ["host:web-1"]
        await pilot.press("escape")
        await pilot.pause()
        assert "host:github.com" in option_ids(app)
        assert app.is_running  # the first escape only cleared the search


@pytest.mark.asyncio
async def test_escape_quits_when_no_search(env, tmp_path):
    marker_dir = tmp_path / "xdg" / "sshinator"
    marker_dir.mkdir(parents=True)
    (marker_dir / "accepted").write_text("accepted\n")
    app = SSHinator(env)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
    assert not app.is_running


@pytest.mark.asyncio
async def test_edit_confirms_then_writes_with_backup(env, tmp_path):
    marker_dir = tmp_path / "xdg" / "sshinator"
    marker_dir.mkdir(parents=True)
    (marker_dir / "accepted").write_text("accepted\n")
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        app.query_one("#hosts").highlighted = option_ids(app).index("host:web-1")
        await pilot.press("e")
        await pilot.pause()
        assert isinstance(app.screen, EditScreen)
        app.screen.query_one("#Port").value = "2200"
        await pilot.click("#save")
        await pilot.pause()
        assert isinstance(app.screen, ShadowBackupScreen)
        assert env.read_text(encoding="utf-8") == SAMPLE
        await pilot.click("#continue")
        await pilot.pause()

    text = env.read_text(encoding="utf-8")
    assert "  Port 2200\n" in text
    assert "# keep this comment" in text
    assert "UseKeychain yes" in text
    backups = list((tmp_path / "xdg" / "sshinator" / "sshinator-backups").glob("shadow_backup-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == SAMPLE
    assert env.stat().st_mode & 0o777 == 0o600


def accept(tmp_path):
    marker_dir = tmp_path / "xdg" / "sshinator"
    marker_dir.mkdir(parents=True)
    (marker_dir / "accepted").write_text("accepted\n")


@pytest.mark.asyncio
async def test_masthead_shows_logo_when_tall_enough(env, tmp_path):
    from textual.widgets import Static

    from sshinator.masthead import LOGO

    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert str(app.query_one("#masthead", Static).render()) == LOGO
        assert app.query_one("#help").region.bottom <= 24
        assert app.query_one("#hosts").region.height >= 3


@pytest.mark.asyncio
async def test_masthead_falls_back_to_one_line_when_short(env, tmp_path):
    from textual.widgets import Static

    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(80, 16)) as pilot:
        await pilot.pause()
        assert str(app.query_one("#masthead", Static).render()) == "SSHinator"


@pytest.mark.asyncio
async def test_help_box_lists_keys(env, tmp_path):
    from textual.widgets import Static

    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        text = str(app.query_one("#help", Static).render())
        for item in ("select: ↑/↓", "connect: ENTER", "expand/details: SPACE", "edit: e",
                     "search: /", "clear/quit: ESC", "reload: CTRL+R", "q quit"):
            assert item in text
        assert "add" not in text.lower()
        assert "delete" not in text.lower()


@pytest.mark.asyncio
async def test_single_hosts_tab_and_row_format(env, tmp_path):
    from textual.widgets import OptionList, TabbedContent

    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert app.query_one(TabbedContent).tab_count == 2
        option_list = app.query_one("#hosts", OptionList)
        prompts = [str(option_list.get_option_at_index(i).prompt) for i in range(option_list.option_count)]
        assert any(p.endswith("10.0.0.12 (web-1)") for p in prompts)
        assert any(p.startswith("▾ ") for p in prompts)
        await pilot.press("left", "right")
        assert app.is_running


@pytest.mark.asyncio
async def test_q_quits_and_space_toggles_group(env, tmp_path):
    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        app.query_one("#hosts").highlighted = option_ids(app).index("group:lab")
        await pilot.press("space")
        assert "host:web-1" not in option_ids(app)
        await pilot.press("q")
        await pilot.pause()
    assert not app.is_running


@pytest.mark.asyncio
async def test_q_types_into_search_and_escape_closes_it(env, tmp_path):
    from textual.widgets import Input

    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        await pilot.press("slash", "q")
        await pilot.pause()
        search = app.query_one("#search", Input)
        assert app.is_running
        assert search.value == "q"
        await pilot.press("escape")
        await pilot.pause()
        assert not search.display
        assert app.is_running


@pytest.mark.asyncio
async def test_q_quits_from_the_host_list(env, tmp_path):
    from textual.widgets import OptionList

    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        app.query_one("#hosts", OptionList).focus()
        await pilot.press("q")
        await pilot.pause()
        assert not app.is_running


KNOWN = (
    "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMq\n"
    "web-1,10.0.0.12 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQ\n"
    "|1|c2FsdA==|aGFzaA== ecdsa-sha2-nistp256 AAAAE2VjZHNh\n"
    "@revoked old.example ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQ\n"
)


@pytest.mark.asyncio
async def test_known_hosts_tab_browses_and_left_right_switch(env, tmp_path):
    from textual.widgets import OptionList, TabbedContent

    accept(tmp_path)
    known = tmp_path / "known_hosts"
    known.write_text(KNOWN, encoding="utf-8")
    app = SSHinator(env, known_hosts=known)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        tabbed = app.query_one(TabbedContent)
        assert tabbed.active == "tab-hosts"
        await pilot.press("right")
        await pilot.pause()
        assert tabbed.active == "tab-known"
        labels = [str(app.query_one("#known", OptionList).get_option_at_index(i).prompt)
                  for i in range(app.query_one("#known", OptionList).option_count)]
        assert "github.com  ssh-ed25519" in labels
        assert "web-1, 10.0.0.12  ssh-rsa" in labels
        assert "(hashed host)  ecdsa-sha2-nistp256" in labels
        assert "@revoked old.example  ssh-rsa" in labels
        # Hosts-only keys do nothing on the Known hosts tab.
        await pilot.press("slash", "space", "e")
        await pilot.pause()
        assert app.is_running
        await pilot.press("left")
        await pilot.pause()
        assert tabbed.active == "tab-hosts"


@pytest.mark.asyncio
async def test_known_hosts_missing_file_says_so(env, tmp_path):
    from textual.widgets import OptionList

    accept(tmp_path)
    app = SSHinator(env, known_hosts=tmp_path / "absent")
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        known = app.query_one("#known", OptionList)
        assert str(known.get_option_at_index(0).prompt) == "No known hosts yet"


async def start_edit(app, pilot):
    await pilot.pause()
    app.query_one("#hosts").highlighted = option_ids(app).index("host:web-1")
    await pilot.press("e")
    await pilot.pause()
    app.screen.query_one("#Port").value = "2200"
    await pilot.click("#save")
    await pilot.pause()


@pytest.mark.asyncio
async def test_shadow_box_cancel_writes_nothing(env, tmp_path):
    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await start_edit(app, pilot)
        assert isinstance(app.screen, ShadowBackupScreen)
        assert app.screen.focused.id == "cancel"
        await pilot.click("#cancel")
        await pilot.pause()
    assert env.read_text(encoding="utf-8") == SAMPLE
    assert not (tmp_path / "xdg" / "sshinator" / "sshinator-backups").exists()


@pytest.mark.asyncio
async def test_shadow_box_text_and_real_backup_name(env, tmp_path):
    from textual.widgets import Static

    from sshinator import paths, warning_text

    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await start_edit(app, pilot)
        text = str(app.screen.query_one("#dialog").query(Static).last().render())
        assert "A destructive action is about to occur." in text
        assert str(env) in text
        assert text.index(warning_text.BUG_MESSAGE) < text.index("Backup folder")
        assert f"Backup folder: {paths.backup_dir()}" in text
        await pilot.click("#continue")
        await pilot.pause()
    (backup,) = paths.backup_dir().glob("shadow_backup-*.bak")
    assert re.fullmatch(r"shadow_backup-\d{8}-\d{6}\.bak", backup.name)
    assert f"Backup file: {backup.name}" in text


@pytest.mark.asyncio
async def test_flag_box_decline_keeps_safe_mode(env, tmp_path):
    from textual.widgets import Static

    accept(tmp_path)
    app = SSHinator(env, dont_blame=True)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, BlameScreen)
        assert app.screen.focused.id == "decline"
        await pilot.click("#decline")
        await pilot.pause()
        assert app.mode == "safe_mode"
        assert app.mode == "safe_mode"
        assert len(app.query("#mode")) == 0
        assert not (tmp_path / "xdg" / "sshinator" / "doofenshmirtz-accepted").exists()
        await start_edit(app, pilot)
        assert isinstance(app.screen, ShadowBackupScreen)


@pytest.mark.asyncio
async def test_flag_box_accept_skips_shadow_box(env, tmp_path):
    from textual.widgets import Static

    accept(tmp_path)
    app = SSHinator(env, dont_blame=True)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        await pilot.click("#accept")
        await pilot.pause()
        assert (tmp_path / "xdg" / "sshinator" / "doofenshmirtz-accepted").read_text().strip() == "dont_blame"
        assert app.mode == "dont_blame"
        assert len(app.query("#mode")) == 0
        await start_edit(app, pilot)
        assert not isinstance(app.screen, ShadowBackupScreen)
    assert "  Port 2200\n" in env.read_text(encoding="utf-8")
    assert len(list((tmp_path / "xdg" / "sshinator" / "sshinator-backups").glob("shadow_backup-*.bak"))) == 1


@pytest.mark.asyncio
async def test_flag_always_asks_even_with_marker(env, tmp_path):
    accept(tmp_path)
    (tmp_path / "xdg" / "sshinator" / "doofenshmirtz-accepted").write_text("accepted\n")
    app = SSHinator(env, dont_blame=True)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, BlameScreen)
        await pilot.click("#accept")
        await pilot.pause()
        assert app.mode == "dont_blame"


@pytest.mark.asyncio
async def test_masthead_class_follows_mode(env, tmp_path):
    from textual.widgets import Static

    accept(tmp_path)
    app = SSHinator(env, dont_blame=True)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        masthead = app.query_one("#masthead", Static)
        assert masthead.has_class("mode-safe") and not masthead.has_class("mode-blame")
        assert masthead.styles.color == Color.parse(app.get_css_variables()["primary"])
        await pilot.click("#accept")
        await pilot.pause()
        assert masthead.has_class("mode-blame") and not masthead.has_class("mode-safe")
        assert str(masthead.styles.color.hex) == "#FF0000"


def blame_file(tmp_path, content=None):
    path = tmp_path / "xdg" / "sshinator" / "doofenshmirtz-accepted"
    if content is not None:
        path.write_text(content)
    return path


@pytest.mark.asyncio
async def test_file_dont_blame_starts_unsafe_without_flag(env, tmp_path):
    accept(tmp_path)
    blame_file(tmp_path, "dont_blame\n")
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert not isinstance(app.screen, BlameScreen)
        assert app.mode == "dont_blame"
        assert app.query_one("#masthead").has_class("mode-blame")


@pytest.mark.asyncio
async def test_old_accepted_content_means_dont_blame(env, tmp_path):
    accept(tmp_path)
    blame_file(tmp_path, "accepted\n")
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert app.mode == "dont_blame"


@pytest.mark.asyncio
async def test_file_safe_starts_safe_without_flag(env, tmp_path):
    accept(tmp_path)
    blame_file(tmp_path, "safe\n")
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert app.mode == "safe_mode"
        assert app.query_one("#masthead").has_class("mode-safe")


@pytest.mark.asyncio
async def test_no_file_no_flag_is_safe(env, tmp_path):
    accept(tmp_path)
    app = SSHinator(env)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert app.mode == "safe_mode"
        assert not blame_file(tmp_path).exists()


@pytest.mark.asyncio
async def test_flag_with_safe_file_asks_then_rewrites(env, tmp_path):
    accept(tmp_path)
    path = blame_file(tmp_path, "safe\n")
    app = SSHinator(env, dont_blame=True)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, BlameScreen)
        await pilot.click("#accept")
        await pilot.pause()
        assert app.mode == "dont_blame"
    assert path.read_text().strip() == "dont_blame"


@pytest.mark.asyncio
async def test_safe_option_overrides_file_and_rewrites(env, tmp_path):
    accept(tmp_path)
    path = blame_file(tmp_path, "dont_blame\n")
    app = SSHinator(env, safe=True)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert app.mode == "safe_mode"
    assert not path.exists()


@pytest.mark.asyncio
async def test_safe_option_without_file_creates_nothing(env, tmp_path):
    accept(tmp_path)
    app = SSHinator(env, safe=True)
    async with app.run_test(size=(120, 50)) as pilot:
        await pilot.pause()
        assert app.mode == "safe_mode"
    assert not blame_file(tmp_path).exists()
