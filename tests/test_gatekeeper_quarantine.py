import json

import pytest

from tools.gatekeeper_quarantine import main


def test_quarantine_and_restore_preserve_bytes(tmp_path, capsys):
    inbox = tmp_path / "exports"
    inbox.mkdir()
    source = inbox / "Example.eml"
    original = b"Subject: Example\r\n\r\nSaved email\r\n"
    source.write_bytes(original)
    quarantine = tmp_path / "quarantine"
    args = ["--directory", str(quarantine)]

    main([*args, "move", str(source)])
    assert not source.exists()
    assert (quarantine / source.name).read_bytes() == original
    capsys.readouterr()

    main([*args, "list"])
    assert json.loads(capsys.readouterr().out) == [source.name]

    main([*args, "restore", source.name, str(inbox)])
    assert source.read_bytes() == original
    assert not (quarantine / source.name).exists()


def test_quarantine_refuses_collisions_and_symlinks(tmp_path, capsys):
    quarantine = tmp_path / "quarantine"
    quarantine.mkdir()
    source = tmp_path / "notice.eml"
    source.write_bytes(b"source")
    stored = quarantine / source.name
    stored.write_bytes(b"quarantined")
    alias = tmp_path / "alias.eml"
    alias.symlink_to(source)
    args = ["--directory", str(quarantine)]

    for invocation, error in [
        (["move", str(source)], "destination already exists"),
        (["restore", stored.name, str(tmp_path)], "destination already exists"),
        (["move", str(alias)], "select a regular .eml file"),
        (["restore", "../notice.eml", str(tmp_path)], "use a quarantined .eml filename"),
    ]:
        with pytest.raises(SystemExit) as exc_info:
            main([*args, *invocation])
        assert exc_info.value.code == 1
        assert error in capsys.readouterr().err

    assert source.read_bytes() == b"source"
    assert stored.read_bytes() == b"quarantined"
    assert alias.is_symlink()
