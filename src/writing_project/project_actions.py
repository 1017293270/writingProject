from __future__ import annotations

from pathlib import Path
from typing import Protocol

from writing_project.files import count_words, read_text
from writing_project.models import Chapter, Project


class ProjectActionRepository(Protocol):
    def create_project(
        self, name: str, genre: str, premise: str, style_guide_path: str, root_dir: str, status: str = "active"
    ) -> int: ...
    def create_chapter(
        self,
        project_id: int,
        volume_no: int,
        chapter_no: int,
        title: str,
        outline: str,
        summary: str = "",
        draft_path: str | None = None,
        final_path: str | None = None,
        status: str = "planned",
        word_count: int = 0,
    ) -> int: ...
    def create_task(
        self,
        project_id: int,
        chapter_id: int,
        task_type: str,
        title: str,
        instruction_path: str,
        context_path: str,
        output_path: str,
        status: str = "pending",
        priority: int = 1,
    ) -> int: ...
    def get_project(self, project_id: int) -> Project: ...
    def get_chapter(self, chapter_id: int) -> Chapter: ...


WORKSPACE_DIRS = [
    "world",
    "entities/characters",
    "entities/locations",
    "entities/factions",
    "entities/items",
    "chapters/v01",
    "tasks",
    "context",
    "outputs",
    "reviews",
]


def create_project(
    repository: ProjectActionRepository, name: str, genre: str, premise: str, root_dir: str | Path
) -> int:
    root = Path(root_dir)
    for relative_dir in WORKSPACE_DIRS:
        (root / relative_dir).mkdir(parents=True, exist_ok=True)
    style_guide_path = root / "world" / "style-guide.md"
    if not style_guide_path.exists():
        style_guide_path.write_text(f"# {name} Style Guide\n", encoding="utf-8")
    return repository.create_project(name, genre, premise, str(style_guide_path), str(root), "active")


def create_chapter(
    repository: ProjectActionRepository,
    project_id: int,
    volume_no: int,
    chapter_no: int,
    title: str,
    outline: str,
) -> int:
    return repository.create_chapter(project_id, volume_no, chapter_no, title, outline, status="planned")


def import_markdown_file(
    repository: ProjectActionRepository,
    project_id: int,
    markdown_path: str | Path,
    volume_no: int,
    chapter_no: int,
) -> int:
    path = Path(markdown_path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file does not exist: {path}")
    content = read_text(path)
    return repository.create_chapter(
        project_id=project_id,
        volume_no=volume_no,
        chapter_no=chapter_no,
        title=path.stem,
        outline="",
        summary="",
        draft_path=str(path),
        final_path=None,
        status="drafted",
        word_count=count_words(content),
    )


def import_markdown_directory(
    repository: ProjectActionRepository,
    project_id: int,
    directory: str | Path,
    volume_no: int,
    start_chapter_no: int,
) -> list[int]:
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"Markdown directory does not exist: {root}")
    imported: list[int] = []
    for offset, markdown_path in enumerate(sorted(root.glob("*.md"))):
        imported.append(import_markdown_file(repository, project_id, markdown_path, volume_no, start_chapter_no + offset))
    return imported


def create_write_task(repository: ProjectActionRepository, chapter_id: int) -> int:
    chapter = repository.get_chapter(chapter_id)
    project = repository.get_project(chapter.project_id)
    root = Path(project.root_dir)
    chapter_label = f"{chapter.chapter_no:03d}"
    task_label = f"{chapter.id:04d}"
    return repository.create_task(
        project_id=project.id,
        chapter_id=chapter.id,
        task_type="write_chapter",
        title=f"写作第 {chapter.volume_no} 卷第 {chapter.chapter_no} 章：{chapter.title}",
        instruction_path=str(root / "tasks" / f"task-{task_label}-write-chapter-{chapter_label}.md"),
        context_path=str(root / "context" / f"context-{task_label}-write-chapter-{chapter_label}.json"),
        output_path=str(root / "outputs" / f"ch{chapter_label}-draft.md"),
        status="pending",
        priority=1,
    )
