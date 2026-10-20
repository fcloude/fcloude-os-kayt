import pytest

from kayt import cli
from kayt.inputs import InputError, check_question, read_file

LIMIT = 100 * 1024


def test_reads_txt_file(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("hello world", encoding="utf-8")
    assert read_file(str(path)) == "hello world"


def test_reads_md_file(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# title", encoding="utf-8")
    assert read_file(str(path)) == "# title"


def test_missing_file_rejected(tmp_path):
    with pytest.raises(InputError, match="not found"):
        read_file(str(tmp_path / "absent.txt"))


def test_directory_rejected(tmp_path):
    with pytest.raises(InputError, match="regular file"):
        read_file(str(tmp_path))


def test_wrong_extension_rejected(tmp_path):
    path = tmp_path / "notes.pdf"
    path.write_text("some text", encoding="utf-8")
    with pytest.raises(InputError, match="unsupported file type"):
        read_file(str(path))


def test_oversized_file_rejected(tmp_path):
    path = tmp_path / "big.txt"
    path.write_bytes(b"a" * (LIMIT + 1))
    with pytest.raises(InputError, match="too large"):
        read_file(str(path))


def test_file_at_size_limit_accepted(tmp_path):
    path = tmp_path / "exactly.txt"
    path.write_bytes(b"a" * LIMIT)
    assert read_file(str(path)) == "a" * LIMIT


def test_non_utf8_file_rejected(tmp_path):
    path = tmp_path / "binary.txt"
    path.write_bytes(b"\xff\x00\xfe")
    with pytest.raises(InputError, match="UTF-8"):
        read_file(str(path))


def test_empty_file_rejected(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")
    with pytest.raises(InputError, match="empty"):
        read_file(str(path))


def test_empty_question_rejected():
    with pytest.raises(InputError, match="question is empty"):
        check_question("   ")


def test_cli_failure_is_one_line_and_exits_nonzero(tmp_path, capsys):
    with pytest.raises(SystemExit) as err:
        cli.main(["what is this?", "--file", str(tmp_path / "absent.txt")])
    assert err.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
    assert captured.err.startswith("error: ")
    assert "Traceback" not in captured.err
