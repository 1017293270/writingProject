from typer.testing import CliRunner

from writing_project.cli import app


def test_cli_help_renders():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "projects" in result.output
    assert "export-task" in result.output
