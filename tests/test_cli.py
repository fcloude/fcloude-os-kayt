import pytest

from kayt import cli


def test_typed_question_reports_typed_text(capsys):
    cli.main(["what is this?"])
    assert capsys.readouterr().out.splitlines() == [
        "Input: typed text",
        "Provider: mock",
        "mock response",
    ]


def test_file_option_reports_filename(tmp_path, capsys):
    path = tmp_path / "notes.txt"
    path.write_text("some notes", encoding="utf-8")
    cli.main(["summarise this", "--file", str(path)])
    assert capsys.readouterr().out.splitlines() == [
        f"Input: file {path}",
        "Provider: mock",
        "mock response",
    ]


def test_symlinked_file_is_rejected(tmp_path, capsys):
    target = tmp_path / "notes.txt"
    target.write_text("some notes", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("this machine cannot create symlinks")
    with pytest.raises(SystemExit) as err:
        cli.main(["what is this?", "--file", str(link)])
    assert err.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
    assert captured.err.startswith("error: ")
    assert "symlink" in captured.err


def test_empty_file_is_rejected_with_one_line_error(tmp_path, capsys):
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit) as err:
        cli.main(["what is this?", "--file", str(path)])
    assert err.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error: file is empty" in captured.err
