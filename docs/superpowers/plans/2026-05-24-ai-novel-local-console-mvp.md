# AI Novel Local Console MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local CLI writing console that reads the existing MySQL novel tables, generates Codex-friendly task/context files, imports Codex output, and records review issues.

**Architecture:** Use a small Python package with focused modules: configuration, MySQL access, path/file operations, context generation, task rendering, output import, and CLI commands. The MVP implements the file bridge first; a web UI can be added later without changing the MySQL + Markdown/JSON protocol.

**Tech Stack:** Python 3.11+, Typer CLI, mysql-connector-python, pytest, python-dotenv, pathlib/json from the standard library.

---

## Scope Check

This plan intentionally implements the first testable subsystem from the approved design: the file bridge core plus a CLI console. It does not build a web interface yet. After this plan is complete, the project can create, inspect, export, and import writing tasks from MySQL and local files.

## File Structure

- Create: `pyproject.toml` - package metadata, CLI entry point, dependencies, pytest config.
- Create: `.env.example` - documented MySQL connection variables.
- Create: `README.md` - setup, database prerequisite, and CLI usage.
- Create: `src/writing_project/__init__.py` - package marker and version.
- Create: `src/writing_project/config.py` - environment loading and typed app settings.
- Create: `src/writing_project/db.py` - MySQL connection factory and row helpers.
- Create: `src/writing_project/models.py` - dataclasses for Project, Chapter, Task, Entity, PlotThread, TimelineEvent.
- Create: `src/writing_project/repositories.py` - SQL reads/writes for existing `ai_novel_%` tables.
- Create: `src/writing_project/files.py` - safe directory creation, JSON/Markdown read-write, CJK-aware word count.
- Create: `src/writing_project/context_builder.py` - builds the `context.json` payload for a task.
- Create: `src/writing_project/task_renderer.py` - renders Codex-facing Markdown task instructions.
- Create: `src/writing_project/importer.py` - imports output Markdown and updates MySQL status.
- Create: `src/writing_project/review_importer.py` - imports structured review issues from JSON.
- Create: `src/writing_project/cli.py` - Typer commands for listing projects/tasks, exporting tasks, importing output, importing review issues.
- Create: `tests/conftest.py` - fake repository fixtures and temp project roots.
- Create: `tests/test_files.py` - filesystem helper tests.
- Create: `tests/test_context_builder.py` - context payload tests.
- Create: `tests/test_task_renderer.py` - task Markdown tests.
- Create: `tests/test_importer.py` - output import behavior tests.
- Create: `tests/test_review_importer.py` - review issue import tests.
- Create: `tests/test_cli.py` - CLI smoke tests with fake services.

## Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/writing_project/__init__.py`

- [ ] **Step 1: Create package metadata**

Add `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "writing-project"
version = "0.1.0"
description = "Local MySQL and file bridge console for Codex-assisted novel writing."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "mysql-connector-python>=9.1.0",
  "python-dotenv>=1.0.1",
  "typer>=0.12.5",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.3",
]

[project.scripts]
writing-project = "writing_project.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-q"
```

- [ ] **Step 2: Create environment template**

Add `.env.example`:

```dotenv
AI_NOVEL_DB_HOST=127.0.0.1
AI_NOVEL_DB_PORT=3306
AI_NOVEL_DB_USER=root
AI_NOVEL_DB_PASSWORD=
AI_NOVEL_DB_NAME=ai_novel_platform
```

- [ ] **Step 3: Create README setup notes**

Add `README.md`:

```markdown
# Writing Project

Local writing console for Codex-assisted long-form fiction.

## Setup

1. Create the MySQL `ai_novel_%` tables from the design SQL.
2. Copy `.env.example` to `.env` and fill in your MySQL credentials.
3. Install dependencies:

```powershell
python -m pip install -e ".[dev]"
```

## Commands

```powershell
writing-project projects
writing-project tasks --project-id 1
writing-project export-task 1
writing-project import-output 1
writing-project import-review 1 E:/ai辅助平台/novels/demo-novel/reviews/review-0001.json
```
```

- [ ] **Step 4: Create package marker**

Add `src/writing_project/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 5: Install and verify package metadata**

Run:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Expected: pytest starts and reports that no tests or current skeleton tests pass. If `pip` cannot reach PyPI, stop and report the network/dependency blocker.

- [ ] **Step 6: Commit**

```powershell
git add pyproject.toml .env.example README.md src/writing_project/__init__.py
git commit -m "chore: scaffold python writing console"
```

## Task 2: Configuration and Database Access

**Files:**
- Create: `src/writing_project/config.py`
- Create: `src/writing_project/db.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Add `tests/test_config.py`:

```python
from writing_project.config import Settings


def test_settings_from_mapping_uses_defaults():
    settings = Settings.from_mapping({"AI_NOVEL_DB_USER": "writer", "AI_NOVEL_DB_NAME": "novels"})

    assert settings.db_host == "127.0.0.1"
    assert settings.db_port == 3306
    assert settings.db_user == "writer"
    assert settings.db_password == ""
    assert settings.db_name == "novels"


def test_settings_connection_config_excludes_database_when_empty():
    settings = Settings(db_user="root", db_name="")

    assert settings.connection_config() == {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "",
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_config.py -q
```

Expected: FAIL because `writing_project.config` does not exist.

- [ ] **Step 3: Implement configuration**

Add `src/writing_project/config.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "ai_novel_platform"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls.from_mapping(os.environ)

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "Settings":
        return cls(
            db_host=values.get("AI_NOVEL_DB_HOST", "127.0.0.1"),
            db_port=int(values.get("AI_NOVEL_DB_PORT", "3306")),
            db_user=values.get("AI_NOVEL_DB_USER", "root"),
            db_password=values.get("AI_NOVEL_DB_PASSWORD", ""),
            db_name=values.get("AI_NOVEL_DB_NAME", "ai_novel_platform"),
        )

    def connection_config(self) -> dict[str, object]:
        config: dict[str, object] = {
            "host": self.db_host,
            "port": self.db_port,
            "user": self.db_user,
            "password": self.db_password,
        }
        if self.db_name:
            config["database"] = self.db_name
        return config
```

- [ ] **Step 4: Implement database helper**

Add `src/writing_project/db.py`:

```python
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection

from writing_project.config import Settings


@contextmanager
def connect(settings: Settings | None = None) -> Iterator[MySQLConnection]:
    active_settings = settings or Settings.from_env()
    connection = mysql.connector.connect(**active_settings.connection_config())
    try:
        yield connection
    finally:
        connection.close()


def fetch_all(connection: MySQLConnection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return list(cursor.fetchall())
    finally:
        cursor.close()


def execute(connection: MySQLConnection, sql: str, params: tuple[Any, ...] = ()) -> int:
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        connection.commit()
        return cursor.rowcount
    finally:
        cursor.close()
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_config.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/writing_project/config.py src/writing_project/db.py tests/test_config.py
git commit -m "feat: add mysql configuration helpers"
```

## Task 3: Domain Models and Repositories

**Files:**
- Create: `src/writing_project/models.py`
- Create: `src/writing_project/repositories.py`
- Create: `tests/test_repositories.py`

- [ ] **Step 1: Write model and repository tests**

Add `tests/test_repositories.py`:

```python
from writing_project.models import Chapter, Project, Task
from writing_project.repositories import row_to_chapter, row_to_project, row_to_task


def test_row_to_project_maps_database_fields():
    project = row_to_project({"id": 1, "name": "Demo", "genre": "玄幻", "premise": "Premise", "style_guide_path": "style.md", "root_dir": "E:/novel", "status": "active"})

    assert project == Project(id=1, name="Demo", genre="玄幻", premise="Premise", style_guide_path="style.md", root_dir="E:/novel", status="active")


def test_row_to_chapter_maps_nullable_paths():
    chapter = row_to_chapter({"id": 2, "project_id": 1, "volume_no": 1, "chapter_no": 3, "title": "Title", "outline": None, "summary": None, "draft_path": None, "final_path": None, "status": "planned", "word_count": 0})

    assert chapter == Chapter(id=2, project_id=1, volume_no=1, chapter_no=3, title="Title", outline="", summary="", draft_path=None, final_path=None, status="planned", word_count=0)


def test_row_to_task_maps_paths_and_priority():
    task = row_to_task({"id": 9, "project_id": 1, "chapter_id": 2, "task_type": "write_chapter", "title": "Write", "instruction_path": "task.md", "context_path": "context.json", "output_path": "out.md", "status": "pending", "priority": 1})

    assert task == Task(id=9, project_id=1, chapter_id=2, task_type="write_chapter", title="Write", instruction_path="task.md", context_path="context.json", output_path="out.md", status="pending", priority=1)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_repositories.py -q
```

Expected: FAIL because models and repositories do not exist.

- [ ] **Step 3: Implement domain models**

Add `src/writing_project/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    genre: str
    premise: str
    style_guide_path: str | None
    root_dir: str
    status: str


@dataclass(frozen=True)
class Chapter:
    id: int
    project_id: int
    volume_no: int
    chapter_no: int
    title: str
    outline: str
    summary: str
    draft_path: str | None
    final_path: str | None
    status: str
    word_count: int


@dataclass(frozen=True)
class Entity:
    id: int
    project_id: int
    entity_type: str
    name: str
    alias: object | None
    description: str
    current_state: str
    detail_path: str | None
    importance: int


@dataclass(frozen=True)
class PlotThread:
    id: int
    project_id: int
    thread_type: str
    title: str
    description: str
    setup_chapter_id: int | None
    payoff_chapter_id: int | None
    status: str
    notes_path: str | None


@dataclass(frozen=True)
class TimelineEvent:
    id: int
    project_id: int
    chapter_id: int | None
    event_order: str
    title: str
    description: str
    involved_entities: object | None
    certainty: str


@dataclass(frozen=True)
class Task:
    id: int
    project_id: int
    chapter_id: int | None
    task_type: str
    title: str
    instruction_path: str
    context_path: str | None
    output_path: str | None
    status: str
    priority: int
```

- [ ] **Step 4: Implement repository functions**

Add `src/writing_project/repositories.py`:

```python
from __future__ import annotations

from typing import Any, Protocol

from writing_project.db import execute, fetch_all
from writing_project.models import Chapter, Entity, PlotThread, Project, Task, TimelineEvent


class ConnectionLike(Protocol):
    def cursor(self, *args: Any, **kwargs: Any) -> Any: ...
    def commit(self) -> None: ...


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def row_to_project(row: dict[str, Any]) -> Project:
    return Project(
        id=int(row["id"]),
        name=str(row["name"]),
        genre=_text(row.get("genre")),
        premise=_text(row.get("premise")),
        style_guide_path=row.get("style_guide_path"),
        root_dir=str(row["root_dir"]),
        status=str(row["status"]),
    )


def row_to_chapter(row: dict[str, Any]) -> Chapter:
    return Chapter(
        id=int(row["id"]),
        project_id=int(row["project_id"]),
        volume_no=int(row["volume_no"]),
        chapter_no=int(row["chapter_no"]),
        title=str(row["title"]),
        outline=_text(row.get("outline")),
        summary=_text(row.get("summary")),
        draft_path=row.get("draft_path"),
        final_path=row.get("final_path"),
        status=str(row["status"]),
        word_count=int(row["word_count"]),
    )


def row_to_entity(row: dict[str, Any]) -> Entity:
    return Entity(
        id=int(row["id"]),
        project_id=int(row["project_id"]),
        entity_type=str(row["entity_type"]),
        name=str(row["name"]),
        alias=row.get("alias"),
        description=_text(row.get("description")),
        current_state=_text(row.get("current_state")),
        detail_path=row.get("detail_path"),
        importance=int(row["importance"]),
    )


def row_to_plot_thread(row: dict[str, Any]) -> PlotThread:
    return PlotThread(
        id=int(row["id"]),
        project_id=int(row["project_id"]),
        thread_type=str(row["thread_type"]),
        title=str(row["title"]),
        description=_text(row.get("description")),
        setup_chapter_id=row.get("setup_chapter_id"),
        payoff_chapter_id=row.get("payoff_chapter_id"),
        status=str(row["status"]),
        notes_path=row.get("notes_path"),
    )


def row_to_timeline_event(row: dict[str, Any]) -> TimelineEvent:
    return TimelineEvent(
        id=int(row["id"]),
        project_id=int(row["project_id"]),
        chapter_id=row.get("chapter_id"),
        event_order=str(row["event_order"]),
        title=str(row["title"]),
        description=_text(row.get("description")),
        involved_entities=row.get("involved_entities"),
        certainty=str(row["certainty"]),
    )


def row_to_task(row: dict[str, Any]) -> Task:
    return Task(
        id=int(row["id"]),
        project_id=int(row["project_id"]),
        chapter_id=row.get("chapter_id"),
        task_type=str(row["task_type"]),
        title=str(row["title"]),
        instruction_path=str(row["instruction_path"]),
        context_path=row.get("context_path"),
        output_path=row.get("output_path"),
        status=str(row["status"]),
        priority=int(row["priority"]),
    )


class NovelRepository:
    def __init__(self, connection: ConnectionLike):
        self.connection = connection

    def list_projects(self) -> list[Project]:
        rows = fetch_all(self.connection, "SELECT id, name, genre, premise, style_guide_path, root_dir, status FROM ai_novel_project ORDER BY id")
        return [row_to_project(row) for row in rows]

    def list_tasks(self, project_id: int, status: str | None = None) -> list[Task]:
        if status:
            rows = fetch_all(self.connection, "SELECT id, project_id, chapter_id, task_type, title, instruction_path, context_path, output_path, status, priority FROM ai_novel_task WHERE project_id = %s AND status = %s ORDER BY priority, id", (project_id, status))
        else:
            rows = fetch_all(self.connection, "SELECT id, project_id, chapter_id, task_type, title, instruction_path, context_path, output_path, status, priority FROM ai_novel_task WHERE project_id = %s ORDER BY priority, id", (project_id,))
        return [row_to_task(row) for row in rows]

    def get_task(self, task_id: int) -> Task:
        rows = fetch_all(self.connection, "SELECT id, project_id, chapter_id, task_type, title, instruction_path, context_path, output_path, status, priority FROM ai_novel_task WHERE id = %s", (task_id,))
        if not rows:
            raise ValueError(f"Task {task_id} not found")
        return row_to_task(rows[0])

    def get_project(self, project_id: int) -> Project:
        rows = fetch_all(self.connection, "SELECT id, name, genre, premise, style_guide_path, root_dir, status FROM ai_novel_project WHERE id = %s", (project_id,))
        if not rows:
            raise ValueError(f"Project {project_id} not found")
        return row_to_project(rows[0])

    def get_chapter(self, chapter_id: int) -> Chapter:
        rows = fetch_all(self.connection, "SELECT id, project_id, volume_no, chapter_no, title, outline, summary, draft_path, final_path, status, word_count FROM ai_novel_chapter WHERE id = %s", (chapter_id,))
        if not rows:
            raise ValueError(f"Chapter {chapter_id} not found")
        return row_to_chapter(rows[0])

    def list_entities(self, project_id: int) -> list[Entity]:
        rows = fetch_all(self.connection, "SELECT id, project_id, entity_type, name, alias, description, current_state, detail_path, importance FROM ai_novel_entity WHERE project_id = %s ORDER BY importance DESC, id", (project_id,))
        return [row_to_entity(row) for row in rows]

    def list_plot_threads(self, project_id: int) -> list[PlotThread]:
        rows = fetch_all(self.connection, "SELECT id, project_id, thread_type, title, description, setup_chapter_id, payoff_chapter_id, status, notes_path FROM ai_novel_plot_thread WHERE project_id = %s ORDER BY id", (project_id,))
        return [row_to_plot_thread(row) for row in rows]

    def list_timeline(self, project_id: int, through_chapter_id: int | None = None) -> list[TimelineEvent]:
        if through_chapter_id:
            rows = fetch_all(self.connection, "SELECT id, project_id, chapter_id, event_order, title, description, involved_entities, certainty FROM ai_novel_timeline_event WHERE project_id = %s AND (chapter_id IS NULL OR chapter_id <= %s) ORDER BY event_order", (project_id, through_chapter_id))
        else:
            rows = fetch_all(self.connection, "SELECT id, project_id, chapter_id, event_order, title, description, involved_entities, certainty FROM ai_novel_timeline_event WHERE project_id = %s ORDER BY event_order", (project_id,))
        return [row_to_timeline_event(row) for row in rows]

    def mark_task_exported(self, task_id: int, context_path: str) -> None:
        execute(self.connection, "UPDATE ai_novel_task SET context_path = %s, status = 'pending' WHERE id = %s", (context_path, task_id))

    def mark_task_completed(self, task_id: int) -> None:
        execute(self.connection, "UPDATE ai_novel_task SET status = 'completed', finished_at = CURRENT_TIMESTAMP WHERE id = %s", (task_id,))

    def update_chapter_draft(self, chapter_id: int, draft_path: str, word_count: int) -> None:
        execute(self.connection, "UPDATE ai_novel_chapter SET draft_path = %s, word_count = %s, status = 'drafted' WHERE id = %s", (draft_path, word_count, chapter_id))

    def create_review_issue(self, project_id: int, chapter_id: int | None, task_id: int | None, issue_type: str, severity: int, title: str, detail: str, suggestion: str) -> None:
        execute(
            self.connection,
            "INSERT INTO ai_novel_review_issue (project_id, chapter_id, task_id, issue_type, severity, title, detail, suggestion, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open')",
            (project_id, chapter_id, task_id, issue_type, severity, title, detail, suggestion),
        )
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_repositories.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/writing_project/models.py src/writing_project/repositories.py tests/test_repositories.py
git commit -m "feat: add novel repository models"
```

## Task 4: File Helpers

**Files:**
- Create: `src/writing_project/files.py`
- Create: `tests/test_files.py`

- [ ] **Step 1: Write failing file helper tests**

Add `tests/test_files.py`:

```python
from pathlib import Path

from writing_project.files import count_words, read_json, write_json, write_text


def test_write_json_creates_parent_directories(tmp_path):
    path = tmp_path / "context" / "task.json"

    write_json(path, {"title": "雪夜入城"})

    assert read_json(path) == {"title": "雪夜入城"}


def test_write_text_creates_parent_directories(tmp_path):
    path = tmp_path / "outputs" / "chapter.md"

    write_text(path, "# 第一章\n风雪压城。")

    assert path.read_text(encoding="utf-8") == "# 第一章\n风雪压城。"


def test_count_words_handles_cjk_and_latin():
    assert count_words("风雪压城 Shen Yan arrived.") == 8
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_files.py -q
```

Expected: FAIL because `writing_project.files` does not exist.

- [ ] **Step 3: Implement file helpers**

Add `src/writing_project/files.py`:

```python
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def ensure_parent(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    target = ensure_parent(path)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_text(path: str | Path, content: str) -> Path:
    target = ensure_parent(path)
    target.write_text(content, encoding="utf-8")
    return target


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def count_words(content: str) -> int:
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", content)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", content)
    return len(cjk_chars) + len(latin_words)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/test_files.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/writing_project/files.py tests/test_files.py
git commit -m "feat: add codex workspace file helpers"
```

## Task 5: Context Builder

**Files:**
- Create: `src/writing_project/context_builder.py`
- Create: `tests/conftest.py`
- Create: `tests/test_context_builder.py`

- [ ] **Step 1: Create fake repository fixture**

Add `tests/conftest.py`:

```python
from dataclasses import dataclass, field

import pytest

from writing_project.models import Chapter, Entity, PlotThread, Project, Task, TimelineEvent


@dataclass
class FakeRepository:
    project: Project = field(default_factory=lambda: Project(1, "示例长篇小说", "玄幻 / 权谋", "少年寻找自身来历。", "E:/novels/demo/world/style-guide.md", "E:/novels/demo", "active"))
    chapter: Chapter = field(default_factory=lambda: Chapter(2, 1, 1, 1, "雪夜入城", "主角抵达寒鸦城。", "前章摘要。", None, None, "planned", 0))
    task: Task = field(default_factory=lambda: Task(9, 1, 2, "write_chapter", "写第一章", "E:/novels/demo/tasks/task-0009.md", "E:/novels/demo/context/context-0009.json", "E:/novels/demo/outputs/ch001.md", "pending", 1))
    created_review_issues: list[dict] = field(default_factory=list)

    def get_task(self, task_id: int) -> Task:
        assert task_id == self.task.id
        return self.task

    def get_project(self, project_id: int) -> Project:
        assert project_id == self.project.id
        return self.project

    def get_chapter(self, chapter_id: int) -> Chapter:
        assert chapter_id == self.chapter.id
        return self.chapter

    def list_entities(self, project_id: int) -> list[Entity]:
        return [
            Entity(1, project_id, "character", "沈砚", ["阿砚"], "男主。", "刚抵达边境城。", "E:/novels/demo/entities/characters/shen-yan.md", 5)
        ]

    def list_plot_threads(self, project_id: int) -> list[PlotThread]:
        return [
            PlotThread(1, project_id, "mystery", "残缺玉牌的来历", "玉牌与旧朝密令有关。", self.chapter.id, None, "open", "E:/novels/demo/plot-threads/jade-token.md")
        ]

    def list_timeline(self, project_id: int, through_chapter_id: int | None = None) -> list[TimelineEvent]:
        return [
            TimelineEvent(1, project_id, self.chapter.id, "1.001", "沈砚雪夜入城", "沈砚抵达寒鸦城。", ["沈砚", "寒鸦城"], "planned")
        ]

    def mark_task_exported(self, task_id: int, context_path: str) -> None:
        self.exported = {"task_id": task_id, "context_path": context_path}


@pytest.fixture
def fake_repository() -> FakeRepository:
    return FakeRepository()
```

- [ ] **Step 2: Write failing context builder tests**

Add `tests/test_context_builder.py`:

```python
from writing_project.context_builder import build_context


def test_build_context_includes_project_chapter_entities_and_output(fake_repository):
    context = build_context(fake_repository, task_id=9)

    assert context["project"]["name"] == "示例长篇小说"
    assert context["chapter"]["title"] == "雪夜入城"
    assert context["entities"][0]["name"] == "沈砚"
    assert context["plot_threads"][0]["title"] == "残缺玉牌的来历"
    assert context["timeline"][0]["title"] == "沈砚雪夜入城"
    assert context["output"]["path"] == "E:/novels/demo/outputs/ch001.md"
    assert context["output"]["format"] == "markdown"
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_context_builder.py -q
```

Expected: FAIL because `context_builder` does not exist.

- [ ] **Step 4: Implement context builder**

Add `src/writing_project/context_builder.py`:

```python
from __future__ import annotations

from typing import Any, Protocol

from writing_project.models import Chapter, Entity, PlotThread, Project, Task, TimelineEvent


class ContextRepository(Protocol):
    def get_task(self, task_id: int) -> Task: ...
    def get_project(self, project_id: int) -> Project: ...
    def get_chapter(self, chapter_id: int) -> Chapter: ...
    def list_entities(self, project_id: int) -> list[Entity]: ...
    def list_plot_threads(self, project_id: int) -> list[PlotThread]: ...
    def list_timeline(self, project_id: int, through_chapter_id: int | None = None) -> list[TimelineEvent]: ...


def build_context(repository: ContextRepository, task_id: int) -> dict[str, Any]:
    task = repository.get_task(task_id)
    if task.chapter_id is None:
        raise ValueError(f"Task {task_id} is not linked to a chapter")

    project = repository.get_project(task.project_id)
    chapter = repository.get_chapter(task.chapter_id)
    entities = repository.list_entities(project.id)
    plot_threads = repository.list_plot_threads(project.id)
    timeline = repository.list_timeline(project.id, through_chapter_id=chapter.id)

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "genre": project.genre,
            "premise": project.premise,
        },
        "chapter": {
            "id": chapter.id,
            "volume_no": chapter.volume_no,
            "chapter_no": chapter.chapter_no,
            "title": chapter.title,
            "outline": chapter.outline,
            "status": chapter.status,
        },
        "style": {
            "style_guide_path": project.style_guide_path,
            "rules": [],
        },
        "entities": [
            {
                "id": entity.id,
                "type": entity.entity_type,
                "name": entity.name,
                "alias": entity.alias,
                "description": entity.description,
                "current_state": entity.current_state,
                "detail_path": entity.detail_path,
                "importance": entity.importance,
            }
            for entity in entities
        ],
        "plot_threads": [
            {
                "id": thread.id,
                "type": thread.thread_type,
                "title": thread.title,
                "description": thread.description,
                "status": thread.status,
                "notes_path": thread.notes_path,
            }
            for thread in plot_threads
        ],
        "timeline": [
            {
                "id": event.id,
                "chapter_id": event.chapter_id,
                "event_order": event.event_order,
                "title": event.title,
                "description": event.description,
                "involved_entities": event.involved_entities,
                "certainty": event.certainty,
            }
            for event in timeline
        ],
        "previous_summary": chapter.summary,
        "constraints": [],
        "output": {
            "path": task.output_path,
            "format": "markdown",
        },
    }
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_context_builder.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/writing_project/context_builder.py tests/conftest.py tests/test_context_builder.py
git commit -m "feat: build codex context payloads"
```

## Task 6: Task Markdown Renderer and Exporter

**Files:**
- Create: `src/writing_project/task_renderer.py`
- Create: `tests/test_task_renderer.py`
- Modify: `src/writing_project/cli.py`

- [ ] **Step 1: Write failing renderer tests**

Add `tests/test_task_renderer.py`:

```python
from writing_project.context_builder import build_context
from writing_project.task_renderer import render_task_markdown


def test_render_task_markdown_contains_paths_and_acceptance(fake_repository):
    context = build_context(fake_repository, 9)
    markdown = render_task_markdown(fake_repository.task, context)

    assert "# 写第一章" in markdown
    assert "任务类型：`write_chapter`" in markdown
    assert "E:/novels/demo/context/context-0009.json" in markdown
    assert "E:/novels/demo/outputs/ch001.md" in markdown
    assert "不要改写或删除上下文包文件" in markdown
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_task_renderer.py -q
```

Expected: FAIL because `task_renderer` does not exist.

- [ ] **Step 3: Implement task renderer**

Add `src/writing_project/task_renderer.py`:

```python
from __future__ import annotations

from typing import Any

from writing_project.models import Task


def render_task_markdown(task: Task, context: dict[str, Any]) -> str:
    chapter = context["chapter"]
    output_path = context["output"]["path"]
    context_path = task.context_path or ""
    return f"""# {task.title}

任务类型：`{task.task_type}`

## 输入文件

- 上下文包：`{context_path}`
- 风格指南：`{context["style"].get("style_guide_path") or "未设置"}`

## 写作目标

- 项目：{context["project"]["name"]}
- 卷号：{chapter["volume_no"]}
- 章节号：{chapter["chapter_no"]}
- 标题：{chapter["title"]}
- 章纲：{chapter["outline"]}

## 输出要求

- 输出路径：`{output_path}`
- 输出格式：Markdown
- 正文应直接写入输出路径。
- 不要改写或删除上下文包文件。
- 不要覆盖最终稿文件。

## 连贯性检查

- 保持人物动机和当前状态一致。
- 遵守时间线顺序。
- 推进或保留上下文包中列出的伏笔。
- 不要引入未解释的关键设定变化。

## 验收标准

- 章节内容与章纲一致。
- 主要角色行为符合上下文中的当前状态。
- 伏笔没有被遗忘或错误回收。
- 输出文件存在且内容为 UTF-8 Markdown。
"""
```

- [ ] **Step 4: Add export service function**

Append to `src/writing_project/task_renderer.py`:

```python
from pathlib import Path

from writing_project.context_builder import ContextRepository, build_context
from writing_project.files import write_json, write_text


def export_task_files(repository: ContextRepository, task_id: int) -> tuple[Path, Path]:
    task = repository.get_task(task_id)
    if task.context_path is None:
        raise ValueError(f"Task {task_id} has no context_path")

    context = build_context(repository, task_id)
    context_path = write_json(task.context_path, context)
    task_markdown = render_task_markdown(task, context)
    instruction_path = write_text(task.instruction_path, task_markdown)

    if hasattr(repository, "mark_task_exported"):
        repository.mark_task_exported(task.id, str(context_path))

    return instruction_path, context_path
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_task_renderer.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/writing_project/task_renderer.py tests/test_task_renderer.py
git commit -m "feat: render codex task files"
```

## Task 7: Output Importer

**Files:**
- Create: `src/writing_project/importer.py`
- Create: `tests/test_importer.py`

- [ ] **Step 1: Write failing importer tests**

Add `tests/test_importer.py`:

```python
from pathlib import Path

import pytest

from writing_project.importer import import_task_output


def test_import_task_output_updates_chapter_and_task(fake_repository, tmp_path):
    output = tmp_path / "ch001.md"
    output.write_text("# 雪夜入城\n风雪压城。", encoding="utf-8")
    fake_repository.task = fake_repository.task.__class__(**{**fake_repository.task.__dict__, "output_path": str(output)})

    result = import_task_output(fake_repository, 9)

    assert result["word_count"] == 5
    assert fake_repository.chapter_update == {"chapter_id": 2, "draft_path": str(output), "word_count": 5}
    assert fake_repository.completed_task_id == 9


def test_import_task_output_fails_when_output_missing(fake_repository, tmp_path):
    fake_repository.task = fake_repository.task.__class__(**{**fake_repository.task.__dict__, "output_path": str(tmp_path / "missing.md")})

    with pytest.raises(FileNotFoundError):
        import_task_output(fake_repository, 9)
```

- [ ] **Step 2: Extend fake repository for importer**

Append to `FakeRepository` in `tests/conftest.py`:

```python
    def update_chapter_draft(self, chapter_id: int, draft_path: str, word_count: int) -> None:
        self.chapter_update = {"chapter_id": chapter_id, "draft_path": draft_path, "word_count": word_count}

    def mark_task_completed(self, task_id: int) -> None:
        self.completed_task_id = task_id
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_importer.py -q
```

Expected: FAIL because `importer` does not exist.

- [ ] **Step 4: Implement importer**

Add `src/writing_project/importer.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from writing_project.files import count_words, read_text
from writing_project.models import Task


class ImportRepository(Protocol):
    def get_task(self, task_id: int) -> Task: ...
    def update_chapter_draft(self, chapter_id: int, draft_path: str, word_count: int) -> None: ...
    def mark_task_completed(self, task_id: int) -> None: ...


def import_task_output(repository: ImportRepository, task_id: int) -> dict[str, object]:
    task = repository.get_task(task_id)
    if task.chapter_id is None:
        raise ValueError(f"Task {task_id} is not linked to a chapter")
    if not task.output_path:
        raise ValueError(f"Task {task_id} has no output_path")

    output_path = Path(task.output_path)
    if not output_path.exists():
        raise FileNotFoundError(f"Output file does not exist: {output_path}")

    content = read_text(output_path)
    word_count = count_words(content)
    repository.update_chapter_draft(task.chapter_id, str(output_path), word_count)
    repository.mark_task_completed(task.id)
    return {"task_id": task.id, "chapter_id": task.chapter_id, "output_path": str(output_path), "word_count": word_count}
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_importer.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/writing_project/importer.py tests/test_importer.py tests/conftest.py
git commit -m "feat: import codex output files"
```

## Task 8: Review Issue Importer

**Files:**
- Create: `src/writing_project/review_importer.py`
- Create: `tests/test_review_importer.py`

- [ ] **Step 1: Write failing review importer tests**

Add `tests/test_review_importer.py`:

```python
import json

from writing_project.review_importer import import_review_issues


def test_import_review_issues_creates_database_rows(fake_repository, tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps({
        "issues": [
            {
                "issue_type": "continuity",
                "severity": 2,
                "title": "玉牌线索断裂",
                "detail": "本章出现玉牌但没有呼应通缉令。",
                "suggestion": "补一处沈砚看到图案后的反应。"
            }
        ]
    }, ensure_ascii=False), encoding="utf-8")

    count = import_review_issues(fake_repository, task_id=9, review_path=review_file)

    assert count == 1
    assert fake_repository.created_review_issues[0]["title"] == "玉牌线索断裂"
    assert fake_repository.created_review_issues[0]["chapter_id"] == 2
```

- [ ] **Step 2: Extend fake repository for review importer**

Append to `FakeRepository` in `tests/conftest.py`:

```python
    def create_review_issue(self, project_id: int, chapter_id: int | None, task_id: int | None, issue_type: str, severity: int, title: str, detail: str, suggestion: str) -> None:
        self.created_review_issues.append({
            "project_id": project_id,
            "chapter_id": chapter_id,
            "task_id": task_id,
            "issue_type": issue_type,
            "severity": severity,
            "title": title,
            "detail": detail,
            "suggestion": suggestion,
        })
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_review_importer.py -q
```

Expected: FAIL because `review_importer` does not exist.

- [ ] **Step 4: Implement review importer**

Add `src/writing_project/review_importer.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from writing_project.files import read_json
from writing_project.models import Task


class ReviewRepository(Protocol):
    def get_task(self, task_id: int) -> Task: ...
    def create_review_issue(self, project_id: int, chapter_id: int | None, task_id: int | None, issue_type: str, severity: int, title: str, detail: str, suggestion: str) -> None: ...


def import_review_issues(repository: ReviewRepository, task_id: int, review_path: str | Path) -> int:
    task = repository.get_task(task_id)
    payload = read_json(review_path)
    issues = payload.get("issues", [])
    if not isinstance(issues, list):
        raise ValueError("Review JSON must contain an 'issues' array")

    for issue in issues:
        repository.create_review_issue(
            project_id=task.project_id,
            chapter_id=task.chapter_id,
            task_id=task.id,
            issue_type=str(issue["issue_type"]),
            severity=int(issue.get("severity", 3)),
            title=str(issue["title"]),
            detail=str(issue.get("detail", "")),
            suggestion=str(issue.get("suggestion", "")),
        )
    return len(issues)
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_review_importer.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/writing_project/review_importer.py tests/test_review_importer.py tests/conftest.py
git commit -m "feat: import structured review issues"
```

## Task 9: CLI Console

**Files:**
- Create: `src/writing_project/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI smoke tests**

Add `tests/test_cli.py`:

```python
from typer.testing import CliRunner

from writing_project.cli import app


def test_cli_help_renders():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "projects" in result.output
    assert "export-task" in result.output
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_cli.py -q
```

Expected: FAIL because `cli.py` does not exist.

- [ ] **Step 3: Implement CLI**

Add `src/writing_project/cli.py`:

```python
from __future__ import annotations

from pathlib import Path

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
    repo._connection_context = connection_context
    return repo


def _close_repository(repo: NovelRepository) -> None:
    context = getattr(repo, "_connection_context", None)
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
```

- [ ] **Step 4: Run CLI tests**

Run:

```powershell
python -m pytest tests/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 5: Run full test suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/writing_project/cli.py tests/test_cli.py
git commit -m "feat: add local writing console cli"
```

## Task 10: Manual MySQL Smoke Test and Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add smoke test documentation**

Append to `README.md`:

```markdown

## Manual Smoke Test

After creating the database tables and seed rows:

```powershell
copy .env.example .env
writing-project projects
writing-project tasks --project-id 1
writing-project export-task 1
```

Open the printed task Markdown file and ask Codex to execute it. After Codex writes the output file:

```powershell
writing-project import-output 1
```

For review issues, create a JSON report:

```json
{
  "issues": [
    {
      "issue_type": "continuity",
      "severity": 2,
      "title": "人物状态不一致",
      "detail": "角色上一章受伤，本章行动没有体现影响。",
      "suggestion": "补充行动受限或恢复原因。"
    }
  ]
}
```

Then run:

```powershell
writing-project import-review 1 E:/ai辅助平台/novels/demo-novel/reviews/review-0001.json
```
```

- [ ] **Step 2: Run tests**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 3: Run live database command**

Run:

```powershell
writing-project projects
```

Expected: prints at least one project row if the seed SQL was inserted, or prints nothing with exit code 0 if the tables are empty. If MySQL credentials are missing, command fails with a clear connector error; fix `.env` and rerun.

- [ ] **Step 4: Commit**

```powershell
git add README.md
git commit -m "docs: add local smoke test workflow"
```

## Task 11: Final Verification and Push

**Files:**
- No new files.

- [ ] **Step 1: Run full tests**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 2: Inspect git state**

Run:

```powershell
git status --short --branch
```

Expected: branch is `main`, working tree is clean, local branch may be ahead of `origin/main`.

- [ ] **Step 3: Push commits**

Run:

```powershell
git push
```

Expected: pushes all implementation commits to `origin/main`.

- [ ] **Step 4: Report completion**

Report:

- Test command and result.
- Whether live `writing-project projects` reached MySQL.
- Last commit hash from `git log --oneline -1`.

## Self-Review

- Spec coverage: The plan covers MySQL access, task/context export, Codex file bridge, output import, review issue import, CLI operations, error cases around missing output files and invalid review JSON, and test coverage. The web UI portion is intentionally deferred because the first testable subsystem is the file bridge core.
- Placeholder scan: No placeholder markers are included.
- Type consistency: `Task`, `Project`, `Chapter`, repository method names, and service signatures are consistent across tasks.
