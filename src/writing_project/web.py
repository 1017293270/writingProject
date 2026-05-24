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
from writing_project.project_actions import (
    create_chapter,
    create_project,
    create_write_task,
    import_markdown_directory,
    import_markdown_file,
)
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

    @app.get("/projects/new", response_class=HTMLResponse)
    def new_project() -> HTMLResponse:
        return HTMLResponse(
            _page("New Project", _top_bar("New Project") + _project_form() + "</main>")
        )

    @app.post("/projects")
    async def create_project_route(request: Request) -> RedirectResponse:
        form = await _form_data(request)
        try:
            with request.app.state.repository_context() as repo:
                project_id = create_project(
                    repo,
                    _required(form, "name"),
                    form.get("genre", ""),
                    form.get("premise", ""),
                    _required(form, "root_dir"),
                )
                return _redirect_project(project_id, "Project created.")
        except Exception as exc:
            return _redirect_error_from_exception(exc)

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
                + _project_actions(project.id)
                + _section("Chapters", _chapter_table(chapters))
                + _section("Tasks", _task_table(tasks))
                + _section("Review Issues", _issue_table(issues))
                + "</main>",
            )

        return _with_repository(request, render)

    @app.get("/projects/{project_id}/chapters/new", response_class=HTMLResponse)
    def new_chapter(request: Request, project_id: int) -> HTMLResponse:
        return _with_repository(
            request,
            lambda repo: _page(
                "New Chapter",
                _top_bar(f"New Chapter · {repo.get_project(project_id).name}")
                + _chapter_form(project_id)
                + "</main>",
            ),
        )

    @app.post("/projects/{project_id}/chapters")
    async def create_chapter_route(request: Request, project_id: int) -> RedirectResponse:
        form = await _form_data(request)
        try:
            with request.app.state.repository_context() as repo:
                create_chapter(
                    repo,
                    project_id,
                    int(_required(form, "volume_no")),
                    int(_required(form, "chapter_no")),
                    _required(form, "title"),
                    form.get("outline", ""),
                )
                return _redirect_project(project_id, "Chapter created.")
        except Exception as exc:
            return _redirect_project(project_id, error=str(exc))

    @app.get("/projects/{project_id}/import", response_class=HTMLResponse)
    def import_page(request: Request, project_id: int) -> HTMLResponse:
        return _with_repository(
            request,
            lambda repo: _page(
                "Import Markdown",
                _top_bar(f"Import · {repo.get_project(project_id).name}")
                + _import_form(project_id)
                + "</main>",
            ),
        )

    @app.post("/projects/{project_id}/import")
    async def import_markdown_route(request: Request, project_id: int) -> RedirectResponse:
        form = await _form_data(request)
        try:
            with request.app.state.repository_context() as repo:
                mode = form.get("mode", "file")
                if mode == "directory":
                    imported = import_markdown_directory(
                        repo,
                        project_id,
                        _required(form, "path"),
                        int(_required(form, "volume_no")),
                        int(_required(form, "start_chapter_no")),
                    )
                    return _redirect_project(project_id, f"Imported {len(imported)} chapters.")
                import_markdown_file(
                    repo,
                    project_id,
                    _required(form, "path"),
                    int(_required(form, "volume_no")),
                    int(_required(form, "start_chapter_no")),
                )
                return _redirect_project(project_id, "Markdown chapter imported.")
        except Exception as exc:
            return _redirect_project(project_id, error=str(exc))

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

    @app.post("/chapters/{chapter_id}/create-task")
    def create_task_for_chapter(request: Request, chapter_id: int) -> RedirectResponse:
        try:
            with request.app.state.repository_context() as repo:
                chapter = repo.get_chapter(chapter_id)
                task_id = create_write_task(repo, chapter_id)
                return _redirect_project(chapter.project_id, f"Task {task_id} created.")
        except Exception as exc:
            return _redirect_error_from_exception(exc)

    return app


async def _form_data(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    from urllib.parse import parse_qs

    return {key: values[-1] for key, values in parse_qs(body, keep_blank_values=True).items()}


def _required(form: dict[str, str], key: str) -> str:
    value = form.get(key, "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _with_repository(request: Request, render: Callable[[Any], str]) -> HTMLResponse:
    try:
        with request.app.state.repository_context() as repo:
            return HTMLResponse(render(repo))
    except MySQLError as exc:
        return HTMLResponse(_page("Database Error", _top_bar() + _error_panel(_friendly_mysql_error(exc))), status_code=503)
    except Exception as exc:
        return HTMLResponse(_page("Error", _top_bar() + _error_panel(str(exc))), status_code=500)


def _redirect_project(project_id: int, message: str | None = None, error: str | None = None) -> RedirectResponse:
    query = ""
    if message:
        query = f"?message={_escape_url(message)}"
    if error:
        query = f"?error={_escape_url(error)}"
    return RedirectResponse(f"/projects/{project_id}{query}", status_code=303)


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
    input, textarea, select {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
      background: white;
      color: var(--text);
    }}
    textarea {{ resize: vertical; }}
    label {{ color: var(--muted); font-weight: 650; }}
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
    create_link = '<div class="actions" style="margin-bottom:14px"><a class="button" href="/projects/new">New Project</a></div>'
    if not projects:
        return create_link + _section("Projects", '<div class="empty">No projects found.</div>') + "</main>"
    rows = "".join(
        f"""<tr>
  <td><a href="/projects/{project.id}">{_h(project.name)}</a></td>
  <td><span class="status">{_h(project.status)}</span></td>
  <td>{_h(project.genre)}</td>
  <td><code>{_h(project.root_dir)}</code></td>
</tr>"""
        for project in projects
    )
    return create_link + _section(
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
  <td><form method="post" action="/chapters/{chapter.id}/create-task"><button class="secondary" type="submit">Create Task</button></form></td>
</tr>"""
        for chapter in chapters
    )
    return f"<table><thead><tr><th>No.</th><th>Title</th><th>Status</th><th>Words</th><th>Draft</th><th>Action</th></tr></thead><tbody>{rows}</tbody></table>"


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


def _project_actions(project_id: int) -> str:
    return f"""<section class="section actions">
  <a class="button" href="/projects/{project_id}/chapters/new">Add Chapter</a>
  <a class="button secondary" href="/projects/{project_id}/import">Import Markdown</a>
</section>"""


def _project_form() -> str:
    return """<section class="section">
  <h2>Create Novel Project</h2>
  <form class="panel detail-grid" method="post" action="/projects">
    <label>Name</label><input name="name" required>
    <label>Genre</label><input name="genre">
    <label>Premise</label><textarea name="premise" rows="4"></textarea>
    <label>Root Directory</label><input name="root_dir" required placeholder="E:/ai辅助平台/novels/my-novel">
    <div></div><button type="submit">Create Project</button>
  </form>
</section>"""


def _chapter_form(project_id: int) -> str:
    return f"""<section class="section">
  <h2>Add Chapter</h2>
  <form class="panel detail-grid" method="post" action="/projects/{project_id}/chapters">
    <label>Volume No.</label><input name="volume_no" type="number" value="1" min="1" required>
    <label>Chapter No.</label><input name="chapter_no" type="number" min="1" required>
    <label>Title</label><input name="title" required>
    <label>Outline</label><textarea name="outline" rows="5"></textarea>
    <div></div><button type="submit">Create Chapter</button>
  </form>
</section>"""


def _import_form(project_id: int) -> str:
    return f"""<section class="section">
  <h2>Import Existing Markdown</h2>
  <form class="panel detail-grid" method="post" action="/projects/{project_id}/import">
    <label>Mode</label>
    <select name="mode">
      <option value="file">Single Markdown file</option>
      <option value="directory">Directory of Markdown files</option>
    </select>
    <label>Path</label><input name="path" required placeholder="E:/ai辅助平台/novels/my-novel/chapters">
    <label>Volume No.</label><input name="volume_no" type="number" value="1" min="1" required>
    <label>Start Chapter No.</label><input name="start_chapter_no" type="number" value="1" min="1" required>
    <div></div><button type="submit">Import</button>
  </form>
</section>"""
