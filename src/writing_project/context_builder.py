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
    def list_previous_chapter_summaries(self, project_id: int, volume_no: int, chapter_no: int, limit: int = 3) -> list[str]: ...


def build_context(repository: ContextRepository, task_id: int) -> dict[str, Any]:
    task = repository.get_task(task_id)
    if task.chapter_id is None:
        raise ValueError(f"Task {task_id} is not linked to a chapter")

    project = repository.get_project(task.project_id)
    chapter = repository.get_chapter(task.chapter_id)
    entities = repository.list_entities(project.id)
    plot_threads = repository.list_plot_threads(project.id)
    timeline = repository.list_timeline(project.id, through_chapter_id=chapter.id)
    previous_summaries = repository.list_previous_chapter_summaries(project.id, chapter.volume_no, chapter.chapter_no)

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
        "previous_summary": "\n".join(previous_summaries),
        "constraints": [],
        "output": {
            "path": task.output_path,
            "format": "markdown",
        },
    }
