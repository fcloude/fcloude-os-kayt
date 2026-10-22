from kayt import cli


def test_cli_runs(tmp_path, capsys):
    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")

    cli.main(["hello", "--file", str(path)])

    out = capsys.readouterr().out.splitlines()
    assert f"File: notes.txt ({path.stat().st_size} bytes)" in out
    assert "Provider: mock" in out
    assert cli.PRIVACY_NOTICE in out
    assert "Summary: hello" in out
