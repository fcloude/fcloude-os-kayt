from kayt import cli


def test_typed_question_reports_typed_text(capsys):
    cli.main(["what is this?"])
    assert capsys.readouterr().out.splitlines() == [
        "Input: typed text",
        "Provider: mock",
        "mock response",
    ]


def test_file_option_reports_filename(capsys):
    cli.main(["summarise this", "--file", "notes.txt"])
    assert capsys.readouterr().out.splitlines() == [
        "Input: file notes.txt",
        "Provider: mock",
        "mock response",
    ]
