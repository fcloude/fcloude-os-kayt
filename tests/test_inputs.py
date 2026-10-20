import pytest

from kayt import cli
from kayt.inputs import InputError, check_question


def test_empty_question_rejected():
    with pytest.raises(InputError, match="question is empty"):
        check_question("   ")


def test_whitespace_only_question_rejected():
    with pytest.raises(InputError, match="question is empty"):
        check_question("\t \n")


def test_cli_failure_is_one_line_and_exits_nonzero(tmp_path, capsys):
    with pytest.raises(SystemExit) as err:
        cli.main(["what is this?", "--file", str(tmp_path / "absent.txt")])
    assert err.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
    assert captured.err.startswith("error: ")
    assert "Traceback" not in captured.err
