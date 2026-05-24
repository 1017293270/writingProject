from __future__ import annotations

import html
import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from mysql.connector import Error as MySQLError

from writing_project.config import Settings
from writing_project.db import connect
from writing_project.importer import import_task_output
from writing_project.repositories import NovelRepository
from writing_project.task_renderer import export_task_files


RepositoryContext = Callable[[], Iterator[Any]]


@contextmanager
def mysql_repository_context() -> Iterator[NovelRepository]:
    with connect(Settings.from_env()) as connection:
        yield NovelRepository(connection)


def create_app(repository_context: RepositoryContext | None = None) -> FastAPI:
    app = FastAPI(title="Writing Project")
    app.state.repository_context = repository_context or mysql_repository_context

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, message: str | None = None, error: str | None = None) -> HTMLResponse:
        return _with_repository(
            request,
            lambda repo: _page(
                "Writing Project",
                _top_bar()
                + _messages(message, error)
                + _project_table(repo.list_projects()),
            ),
        )

    @app.get("/projects/{project_id}", response_class=HTMLResponse)
    def project_detail(
        request: Request, project_id: int, message: str | None = None, error: str | None = None
    ) -> HTMLResponse:
        def render(repo: Any) -> str:
            project = repo.get_project(project_id)
            chapters = repo.list_chapters(project_id)
            tasks = repo.list_tasks(project_id)
            issues = repo.list_review_issues(project_id)
            return _page(
                project.name,
                _top_bar(project.name)
                + _messages(message, error)
                + _section("Chapters", _chapter_table(chapters))
                + _section("Tasks", _task_table(tasks))
                + _section("Review Issues", _issue_table(issues)),
            )

        return _with_repository(request, render)

    @app.get("/tasks/{task_id}", response_class=HTMLResponse)
    def task_detail(request: Request, task_id: int) -> HTMLResponse:
        def render(repo: Any) -> str:
            task = repo.get_task(task_id)
            project = repo.get_project(task.project_id)
            chapter = repo.get_chapter(task.chapter_id) if task.chapter_id else None
            return _page(
                task.title,
                _top_bar(task.title)
                + _task_detail(project, task, chapter),
            )

        return _with_repository(request, render)

    @app.post("/tasks/{task_id}/export")
    def export_task(request: Request, task_id: int) -> RedirectResponse:
        try:
            with request.app.state.repository_context() as repo:
                task = repo.get_task(task_id)
                export_task_files(repo, task_id)
                return _redirect_project(task.project_id, message=f"Task {task_id} exported.")
        except Exception as exc:
            return _redirect_error_from_exception(exc)

    @app.post("/tasks/{task_id}/import-output")
    def import_output(request: Request, task_id: int) -> RedirectResponse:
        try:
            with request.app.state.repository_context() as repo:
                task = repo.get_task(task_id)
                result = import_task_output(repo, task_id)
                return _redirect_project(task.project_id, message=f"Imported {result['word_count']} words.")
        except Exception as exc:
            return _redirect_error_from_exception(exc)

    return app


def _with_repository(request: Request, render: Callable[[Any], str]) -> HTMLResponse:
    try:
        with request.app.state.repository_context() as repo:
            return HTMLResponse(render(repo))
    except MySQLError as exc:
        return HTMLResponse(_page("Database Error", _top_bar() + _error_panel(_friendly_mysql_error(exc))), status_code=503)
    except Exception as exc:
        return HTMLResponse(_page("Error", _top_bar() + _error_panel(str(exc))), status_code=500)


def _redirect_project(project_id: int, message: str) -> RedirectResponse:
    return RedirectResponse(f"/projects/{project_id}?message={_escape_url(message)}", status_code=303)


def _redirect_error_from_exception(exc: Exception) -> RedirectResponse:
    detail = _friendly_mysql_error(exc) if isinstance(exc, MySQLError) else str(exc)
    return RedirectResponse(f"/?error={_escape_url(detail)}", status_code=303)


def _friendly_mysql_error(exc: Exception) -> str:
    return f"MySQL connection failed: {exc}. Check database service, host, port, credentials, and database name."


def _escape_url(value: str) -> str:
    from urllib.parse import quote

    return quote(value)


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_h(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #667085;
      --line: #d9dee7;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --danger: #b42318;
      --warn: #b54708;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 28px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    main {{ width: min(1180px, calc(100vw - 32px)); margin: 24px auto 48px; }}
    h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 17px; letter-spacing: 0; }}
    a {{ color: var(--accent-strong); text-decoration: none; }}
    .muted {{ color: var(--muted); }}
    .section {{ margin-top: 20px; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; font-weight: 650; text-transform: uppercase; }}
    tr:last-child td {{ border-bottom: 0; }}
    code {{ font: 12px/1.4 ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap: anywhere; }}
    .status {{ display: inline-block; min-width: 72px; color: var(--muted); }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    button, .button {{
      border: 1px solid var(--accent);
      background: var(--accent);
      color: white;
      border-radius: 6px;
      padding: 7px 10px;
      font: inherit;
      cursor: pointer;
      min-height: 34px;
    }}
    .button.secondary, button.secondary {{ background: white; color: var(--accent-strong); }}
    .message, .error {{
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 14px;
      background: #ecfdf3;
      border: 1px solid #abefc6;
      color: #067647;
    }}
    .error {{ background: #fef3f2; border-color: #fecdca; color: var(--danger); }}
    .empty {{ padding: 16px; color: var(--muted); }}
    .detail-grid {{ display: grid; grid-template-columns: 160px 1fr; gap: 8px 14px; padding: 16px; }}
    @media (max-width: 760px) {{
      header {{ padding: 14px 16px; align-items: flex-start; flex-direction: column; }}
      main {{ width: calc(100vw - 20px); margin-top: 14px; }}
      table {{ min-width: 760px; }}
      .panel {{ overflow-x: auto; }}
      .detail-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
{body}
</body>
</html>"""


def _top_bar(title: str = "Writing Project") -> str:
    return f"""<header>
  <div>
    <h1>{_h(title)}</h1>
    <div class="muted">Local Codex writing console</div>
  </div>
  <nav><a class="button secondary" href="/">Projects</a></nav>
</header><main>"""


def _section(title: str, content: str) -> str:
    return f'<section class="section"><h2>{_h(title)}</h2><div class="panel">{content}</div></section>'


def _messages(message: str | None, error: str | None) -> str:
    chunks = []
    if message:
        chunks.append(f'<div class="message">{_h(message)}</div>')
    if error:
        chunks.append(f'<div class="error">{_h(error)}</div>')
    return "".join(chunks)


def _error_panel(message: str) -> str:
    return f'<div class="error">{_h(message)}</div></main>'


def _project_table(projects: list[Any]) -> str:
    if not projects:
        return _section("Projects", '<div class="empty">No projects found.</div>') + "</main>"
    rows = "".join(
        f"""<tr>
  <td><a href="/projects/{project.id}">{_h(project.name)}</a></td>
  <td><span class="status">{_h(project.status)}</span></td>
  <td>{_h(project.genre)}</td>
  <td><code>{_h(project.root_dir)}</code></td>
</tr>"""
        for project in projects
    )
    return _section(
        "Projects",
        f"<table><thead><tr><th>Name</th><th>Status</th><th>Genre</th><th>Root</th></tr></thead><tbody>{rows}</tbody></table>",
    ) + "</main>"


def _chapter_table(chapters: list[Any]) -> str:
    if not chapters:
        return '<div class="empty">No chapters found.</div>'
    rows = "".join(
        f"""<tr>
  <td>V{chapter.volume_no} · C{chapter.chapter_no}</td>
  <td>{_h(chapter.title)}</td>
  <td><span class="status">{_h(chapter.status)}</span></td>
  <td>{chapter.word_count}</td>
  <td><code>{_h(chapter.draft_path or "")}</code></td>
</tr>"""
        for chapter in chapters
    )
    return f"<table><thead><tr><th>No.</th><th>Title</th><th>Status</th><th>Words</th><th>Draft</th></tr></thead><tbody>{rows}</tbody></table>"


def _task_table(tasks: list[Any]) -> str:
    if not tasks:
        return '<div class="empty">No tasks found.</div>'
    rows = "".join(
        f"""<tr>
  <td><a href="/tasks/{task.id}">#{task.id}</a></td>
  <td>{_h(task.title)}</td>
  <td>{_h(task.task_type)}</td>
  <td><span class="status">{_h(task.status)}</span></td>
  <td>{task.priority}</td>
  <td class="actions">
    <form method="post" action="/tasks/{task.id}/export"><button type="submit">Export</button></form>
    <form method="post" action="/tasks/{task.id}/import-output"><button class="secondary" type="submit">Import</button></form>
  </td>
</tr>"""
        for task in tasks
    )
    return f"<table><thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Status</th><th>Priority</th><th>Actions</th></tr></thead><tbody>{rows}</tbody></table>"


def _issue_table(issues: list[Any]) -> str:
    if not issues:
        return '<div class="empty">No review issues found.</div>'
    rows = "".join(
        f"""<tr>
  <td>{_h(issue.issue_type)}</td>
  <td>{issue.severity}</td>
  <td>{_h(issue.title)}</td>
  <td><span class="status">{_h(issue.status)}</span></td>
</tr>"""
        for issue in issues
    )
    return f"<table><thead><tr><th>Type</th><th>Severity</th><th>Title</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>"


def _task_detail(project: Any, task: Any, chapter: Any | None) -> str:
    chapter_title = chapter.title if chapter else "No linked chapter"
    payload = {
        "project": project.name,
        "chapter": chapter_title,
        "task_type": task.task_type,
        "status": task.status,
        "instruction_path": task.instruction_path,
        "context_path": task.context_path,
        "output_path": task.output_path,
    }
    details = "".join(f"<dt>{_h(key)}</dt><dd><code>{_h(str(value or ''))}</code></dd>" for key, value in payload.items())
    return f"""<section class="section">
  <h2>Task Detail</h2>
  <div class="panel"><dl class="detail-grid">{details}</dl></div>
</section>
<section class="section actions">
  <form method="post" action="/tasks/{task.id}/export"><button type="submit">Export task files</button></form>
  <form method="post" action="/tasks/{task.id}/import-output"><button class="secondary" type="submit">Import output</button></form>
</section></main>"""


def _h(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)
