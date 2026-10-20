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
