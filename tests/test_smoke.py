from kayt import cli


def test_cli_runs(capsys):
    cli.main(["hello"])
    assert "Provider: mock" in capsys.readouterr().out
