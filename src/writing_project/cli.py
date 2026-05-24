from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from writing_project.config import Settings
from writing_project.db import connect
from writing_project.importer import import_task_output
from writing_project.repositories import NovelRepository
from writing_project.review_importer import import_review_issues
from writing_project.task_renderer import export_task_files

app = typer.Typer(help="Local writing console for Codex-assisted novels.")


def _repository() -> NovelRepository:
    connection_context = connect(Settings.from_env())
    connection = connection_context.__enter__()
    repo = NovelRepository(connection)
    setattr(repo, "_connection_context", connection_context)
    return repo


def _close_repository(repo: NovelRepository) -> None:
    context: Any = getattr(repo, "_connection_context", None)
    if context is not None:
        context.__exit__(None, None, None)


@app.command()
def projects() -> None:
    """List novel projects."""
    repo = _repository()
    try:
        for project in repo.list_projects():
            typer.echo(f"{project.id}\t{project.status}\t{project.name}\t{project.root_dir}")
    finally:
        _close_repository(repo)


@app.command()
def tasks(project_id: int, status: str | None = typer.Option(None, help="Filter by task status.")) -> None:
    """List tasks for a project."""
    repo = _repository()
    try:
        for task in repo.list_tasks(project_id, status=status):
            typer.echo(f"{task.id}\t{task.status}\t{task.priority}\t{task.task_type}\t{task.title}")
    finally:
        _close_repository(repo)


@app.command("export-task")
def export_task(task_id: int) -> None:
    """Generate task Markdown and context JSON for Codex."""
    repo = _repository()
    try:
        instruction_path, context_path = export_task_files(repo, task_id)
        typer.echo(f"task={instruction_path}")
        typer.echo(f"context={context_path}")
    finally:
        _close_repository(repo)


@app.command("import-output")
def import_output(task_id: int) -> None:
    """Import a Codex output Markdown file and update MySQL state."""
    repo = _repository()
    try:
        result = import_task_output(repo, task_id)
        typer.echo(f"imported={result['output_path']}")
        typer.echo(f"word_count={result['word_count']}")
    finally:
        _close_repository(repo)


@app.command("import-review")
def import_review(task_id: int, review_path: Path) -> None:
    """Import structured review issues from a JSON report."""
    repo = _repository()
    try:
        count = import_review_issues(repo, task_id, review_path)
        typer.echo(f"issues_imported={count}")
    finally:
        _close_repository(repo)
