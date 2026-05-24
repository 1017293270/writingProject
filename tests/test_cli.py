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


def test_import_output_reports_missing_file(monkeypatch, fake_repository, tmp_path):
    fake_repository.task = fake_repository.task.__class__(
        **{**fake_repository.task.__dict__, "output_path": str(tmp_path / "missing.md")}
    )
    monkeypatch.setattr(cli, "_repository", lambda: fake_repository)

    result = CliRunner().invoke(app, ["import-output", "9"])

    assert result.exit_code != 0
    assert "Output file does not exist" in result.output


def test_import_review_reports_invalid_json(monkeypatch, fake_repository, tmp_path):
    review_file = tmp_path / "bad.json"
    review_file.write_text("{", encoding="utf-8")
    monkeypatch.setattr(cli, "_repository", lambda: fake_repository)

    result = CliRunner().invoke(app, ["import-review", "9", str(review_file)])

    assert result.exit_code != 0
    assert "Expecting property name" in result.output
