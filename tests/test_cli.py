from click.testing import CliRunner
from chmaquina import cli


def test_help_call():
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    assert result.exit_code == 0
