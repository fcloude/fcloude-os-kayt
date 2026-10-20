from kayt import cli


def test_cli_prints_ready(capsys):
    cli.main()
    assert capsys.readouterr().out.strip() == "KAYT ready"
