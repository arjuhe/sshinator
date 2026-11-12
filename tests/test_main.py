import sys

import pytest

from sshinator import __main__ as cli


@pytest.fixture
def marker(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    path = tmp_path / "xdg" / "sshinator" / "accepted"
    path.parent.mkdir(parents=True)
    path.write_text("accepted\n", encoding="utf-8")
    return path


def run_cli(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["sshinator", *args])
    cli.main()


def test_reset_removes_the_acceptance_marker(marker, monkeypatch, capsys):
    run_cli(monkeypatch, "--reset")
    assert not marker.exists()
    assert "The warning will show again" in capsys.readouterr().out


def test_reset_without_marker_says_nothing_to_reset(marker, monkeypatch, capsys):
    marker.unlink()
    run_cli(monkeypatch, "--reset")
    assert "Nothing to reset" in capsys.readouterr().out


def test_reset_does_not_start_the_app(marker, monkeypatch):
    started = []
    monkeypatch.setattr(cli, "SSHinator", lambda path: started.append(path))
    run_cli(monkeypatch, "--reset")
    assert started == []


def test_flag_without_gate_refuses(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    started = []
    monkeypatch.setattr(cli, "SSHinator", lambda *a, **k: started.append(a))
    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, "--dont-blame-doofenshmirtz")
    assert exit_info.value.code == 2
    assert "needs the warning gate accepted first" in capsys.readouterr().err
    assert started == []
    assert not (tmp_path / "xdg").exists()


def test_reset_removes_both_markers(marker, monkeypatch, capsys):
    blame = marker.parent / "doofenshmirtz-accepted"
    blame.write_text("accepted\n", encoding="utf-8")
    run_cli(monkeypatch, "--reset", "--dont-blame-doofenshmirtz")
    assert not marker.exists() and not blame.exists()
    out = capsys.readouterr().out
    assert str(marker) in out and str(blame) in out


def test_accept_alone_writes_marker(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    started = []
    monkeypatch.setattr(cli, "SSHinator", lambda *a, **k: started.append(a))
    run_cli(monkeypatch, "--accept")
    assert (tmp_path / "xdg" / "sshinator" / "accepted").read_text() == "accepted\n"
    assert started == []
    assert "Accepted" in capsys.readouterr().out
    run_cli(monkeypatch, "--accept")
    assert "already accepted" in capsys.readouterr().out


@pytest.mark.parametrize("other", [["--config", "/tmp/x"], ["--reset"], ["--dont-blame-doofenshmirtz"], ["--safe"]])
def test_accept_cannot_be_combined(tmp_path, monkeypatch, capsys, other):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, "--accept", *other)
    assert exit_info.value.code == 2
    assert "--accept cannot be combined" in capsys.readouterr().err
    assert not (tmp_path / "xdg").exists()


@pytest.mark.parametrize("other", [["--dont-blame-doofenshmirtz"], ["--reset"]])
def test_safe_cannot_be_combined(marker, monkeypatch, other):
    started = []
    monkeypatch.setattr(cli, "SSHinator", lambda *a, **k: started.append(a))
    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, "--safe", *other)
    assert exit_info.value.code == 2
    assert started == [] and marker.exists()


def test_safe_with_config_passes_flag(marker, monkeypatch):
    seen = {}
    monkeypatch.setattr(cli, "SSHinator", lambda path, **k: seen.update(path=path, **k) or type("A", (), {"run": lambda self: None})())
    run_cli(monkeypatch, "--safe", "--config", "/tmp/x")
    assert seen["safe"] is True and seen["dont_blame"] is False
