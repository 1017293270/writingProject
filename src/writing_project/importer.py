from __future__ import annotations

from pathlib import Path
from typing import Protocol

from writing_project.files import count_words, read_text
from writing_project.models import Chapter, Task


class ImportRepository(Protocol):
    def get_task(self, task_id: int) -> Task: ...
    def get_chapter(self, chapter_id: int) -> Chapter: ...
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
    chapter = repository.get_chapter(task.chapter_id)
    if _is_final_chapter(chapter):
        raise ValueError(f"Chapter {chapter.id} already has final content; refusing to overwrite draft state")

    if hasattr(repository, "complete_task_output"):
        repository.complete_task_output(task.id, task.chapter_id, str(output_path), word_count)
    else:
        repository.update_chapter_draft(task.chapter_id, str(output_path), word_count)
        repository.mark_task_completed(task.id)
    return {"task_id": task.id, "chapter_id": task.chapter_id, "output_path": str(output_path), "word_count": word_count}


def _is_final_chapter(chapter: Chapter) -> bool:
    return bool(chapter.final_path) or chapter.status.lower() in {"final", "finalized", "completed", "published"}
