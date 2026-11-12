from sshinator.knownhosts import HASHED, read_known_hosts


def test_parses_names_key_types_and_markers(tmp_path):
    path = tmp_path / "known_hosts"
    path.write_text(
        "# a comment\n"
        "\n"
        "github.com ssh-ed25519 AAAA\n"
        "web-1,10.0.0.12 ssh-rsa AAAA\n"
        "[bastion]:2222 ssh-ed25519 AAAA\n"
        "|1|salt|hash ecdsa-sha2-nistp256 AAAA\n"
        "@cert-authority *.lan ssh-ed25519 AAAA\n"
        "short line\n",
        encoding="utf-8",
    )
    entries = read_known_hosts(path)
    assert [(e.hosts, e.key_type, e.marker) for e in entries] == [
        ("github.com", "ssh-ed25519", ""),
        ("web-1, 10.0.0.12", "ssh-rsa", ""),
        ("[bastion]:2222", "ssh-ed25519", ""),
        (HASHED, "ecdsa-sha2-nistp256", ""),
        ("*.lan", "ssh-ed25519", "@cert-authority"),
    ]


def test_missing_file_gives_no_entries(tmp_path):
    assert read_known_hosts(tmp_path / "nope") == []
