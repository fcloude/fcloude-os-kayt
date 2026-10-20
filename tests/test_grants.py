from pathlib import Path

import pytest

from kayt.grants import Grant, GrantError, GrantStore


def make_notes(tmp_path: Path, text: str = "hello world") -> Path:
    path = tmp_path / "notes.txt"
    path.write_text(text, encoding="utf-8")
    return path


def test_create_returns_grant_and_content(tmp_path):
    grant, content = GrantStore().create(make_notes(tmp_path))
    assert isinstance(grant, Grant)
    assert grant.id == "grant_1"
    assert content == "hello world"


def test_grant_records_resolved_path_and_size(tmp_path):
    path = make_notes(tmp_path, "hello world")
    grant, _ = GrantStore().create(path)
    assert grant.path == path.resolve()
    assert grant.size == len("hello world")


def test_missing_file_rejected(tmp_path):
    with pytest.raises(GrantError, match="not found"):
        GrantStore().create(tmp_path / "absent.txt")


def test_directory_rejected(tmp_path):
    with pytest.raises(GrantError, match="regular file"):
        GrantStore().create(tmp_path)


def test_wrong_extension_rejected(tmp_path):
    path = tmp_path / "notes.pdf"
    path.write_text("some text", encoding="utf-8")
    with pytest.raises(GrantError, match="unsupported file type"):
        GrantStore().create(path)


def test_oversized_file_rejected(tmp_path):
    path = tmp_path / "big.txt"
    path.write_bytes(b"a" * (100 * 1024 + 1))
    with pytest.raises(GrantError, match="too large"):
        GrantStore().create(path)


def test_non_utf8_file_rejected(tmp_path):
    path = tmp_path / "binary.txt"
    path.write_bytes(b"\xff\x00\xfe")
    with pytest.raises(GrantError, match="UTF-8"):
        GrantStore().create(path)


def test_empty_file_rejected(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")
    with pytest.raises(GrantError, match="empty"):
        GrantStore().create(path)


def test_symlink_rejected(tmp_path):
    target = make_notes(tmp_path)
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("this machine cannot create symlinks")
    with pytest.raises(GrantError, match="symlink"):
        GrantStore().create(link)


def test_invented_grant_id_rejected():
    store = GrantStore()
    with pytest.raises(GrantError, match="unknown grant"):
        store.lookup("grant_99")
    with pytest.raises(GrantError, match="unknown grant"):
        store.read("grant_99")


def test_clear_expires_grants(tmp_path):
    store = GrantStore()
    grant, _ = store.create(make_notes(tmp_path))
    assert store.read(grant.id) == "hello world"
    store.clear()
    with pytest.raises(GrantError, match="unknown grant"):
        store.lookup(grant.id)
    with pytest.raises(GrantError, match="unknown grant"):
        store.read(grant.id)


def test_ids_are_not_reused_after_clear(tmp_path):
    path = make_notes(tmp_path)
    store = GrantStore()
    store.create(path)
    store.clear()
    grant, _ = store.create(path)
    assert grant.id == "grant_2"


def test_content_is_snapshotted_at_grant_time(tmp_path):
    path = make_notes(tmp_path, "original")
    store = GrantStore()
    grant, _ = store.create(path)
    path.write_text("swapped out", encoding="utf-8")
    assert store.read(grant.id) == "original"
