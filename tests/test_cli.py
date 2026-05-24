from typer.testing import CliRunner

import writing_project.cli as cli
from writing_project.cli import app


def test_cli_help_renders():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "projects" in result.output
    assert "export-task" in result.output


def test_projects_reports_mysql_connection_failure(monkeypatch):
    def fail_repository():
        raise cli.click.ClickException("MySQL connection failed: cannot connect")

    monkeypatch.setattr(cli, "_repository", fail_repository)

    result = CliRunner().invoke(app, ["projects"])

    assert result.exit_code != 0
    assert "MySQL connection failed" in result.output
