from __future__ import annotations

from typing import Any, Protocol

from writing_project.db import execute, fetch_all
from writing_project.models import Chapter, Entity, PlotThread, Project, Task, TimelineEvent


class ConnectionLike(Protocol):
    def cursor(self, *args: Any, **kwargs: Any) -> Any: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


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
        rows = fetch_all(
            self.connection,
            "SELECT id, name, genre, premise, style_guide_path, root_dir, status "
            "FROM ai_novel_project ORDER BY id",
        )
        return [row_to_project(row) for row in rows]

    def list_tasks(self, project_id: int, status: str | None = None) -> list[Task]:
        if status:
            rows = fetch_all(
                self.connection,
                "SELECT id, project_id, chapter_id, task_type, title, instruction_path, context_path, "
                "output_path, status, priority FROM ai_novel_task WHERE project_id = %s AND status = %s "
                "ORDER BY priority, id",
                (project_id, status),
            )
        else:
            rows = fetch_all(
                self.connection,
                "SELECT id, project_id, chapter_id, task_type, title, instruction_path, context_path, "
                "output_path, status, priority FROM ai_novel_task WHERE project_id = %s ORDER BY priority, id",
                (project_id,),
            )
        return [row_to_task(row) for row in rows]

    def get_task(self, task_id: int) -> Task:
        rows = fetch_all(
            self.connection,
            "SELECT id, project_id, chapter_id, task_type, title, instruction_path, context_path, "
            "output_path, status, priority FROM ai_novel_task WHERE id = %s",
            (task_id,),
        )
        if not rows:
            raise ValueError(f"Task {task_id} not found")
        return row_to_task(rows[0])

    def get_project(self, project_id: int) -> Project:
        rows = fetch_all(
            self.connection,
            "SELECT id, name, genre, premise, style_guide_path, root_dir, status "
            "FROM ai_novel_project WHERE id = %s",
            (project_id,),
        )
        if not rows:
            raise ValueError(f"Project {project_id} not found")
        return row_to_project(rows[0])

    def get_chapter(self, chapter_id: int) -> Chapter:
        rows = fetch_all(
            self.connection,
            "SELECT id, project_id, volume_no, chapter_no, title, outline, summary, draft_path, final_path, "
            "status, word_count FROM ai_novel_chapter WHERE id = %s",
            (chapter_id,),
        )
        if not rows:
            raise ValueError(f"Chapter {chapter_id} not found")
        return row_to_chapter(rows[0])

    def list_entities(self, project_id: int) -> list[Entity]:
        rows = fetch_all(
            self.connection,
            "SELECT id, project_id, entity_type, name, alias, description, current_state, detail_path, importance "
            "FROM ai_novel_entity WHERE project_id = %s ORDER BY importance DESC, id",
            (project_id,),
        )
        return [row_to_entity(row) for row in rows]

    def list_plot_threads(self, project_id: int) -> list[PlotThread]:
        rows = fetch_all(
            self.connection,
            "SELECT id, project_id, thread_type, title, description, setup_chapter_id, payoff_chapter_id, "
            "status, notes_path FROM ai_novel_plot_thread WHERE project_id = %s ORDER BY id",
            (project_id,),
        )
        return [row_to_plot_thread(row) for row in rows]

    def list_timeline(self, project_id: int, through_chapter_id: int | None = None) -> list[TimelineEvent]:
        if through_chapter_id:
            rows = fetch_all(
                self.connection,
                "SELECT id, project_id, chapter_id, event_order, title, description, involved_entities, certainty "
                "FROM ai_novel_timeline_event WHERE project_id = %s AND (chapter_id IS NULL OR chapter_id <= %s) "
                "ORDER BY event_order",
                (project_id, through_chapter_id),
            )
        else:
            rows = fetch_all(
                self.connection,
                "SELECT id, project_id, chapter_id, event_order, title, description, involved_entities, certainty "
                "FROM ai_novel_timeline_event WHERE project_id = %s ORDER BY event_order",
                (project_id,),
            )
        return [row_to_timeline_event(row) for row in rows]

    def list_previous_chapter_summaries(
        self, project_id: int, volume_no: int, chapter_no: int, limit: int = 3
    ) -> list[str]:
        rows = fetch_all(
            self.connection,
            "SELECT summary FROM ai_novel_chapter "
            "WHERE project_id = %s AND summary IS NOT NULL AND summary <> '' "
            "AND (volume_no < %s OR (volume_no = %s AND chapter_no < %s)) "
            "ORDER BY volume_no DESC, chapter_no DESC LIMIT %s",
            (project_id, volume_no, volume_no, chapter_no, limit),
        )
        return [str(row["summary"]) for row in reversed(rows)]

    def mark_task_exported(self, task_id: int, context_path: str) -> None:
        execute(
            self.connection,
            "UPDATE ai_novel_task SET context_path = %s, status = 'pending' WHERE id = %s",
            (context_path, task_id),
        )

    def mark_task_completed(self, task_id: int) -> None:
        execute(
            self.connection,
            "UPDATE ai_novel_task SET status = 'completed', finished_at = CURRENT_TIMESTAMP WHERE id = %s",
            (task_id,),
        )

    def update_chapter_draft(self, chapter_id: int, draft_path: str, word_count: int) -> None:
        execute(
            self.connection,
            "UPDATE ai_novel_chapter SET draft_path = %s, word_count = %s, status = 'drafted' WHERE id = %s",
            (draft_path, word_count, chapter_id),
        )

    def complete_task_output(self, task_id: int, chapter_id: int, draft_path: str, word_count: int) -> None:
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT chapter_id FROM ai_novel_task WHERE id = %s FOR UPDATE", (task_id,))
            task = cursor.fetchone()
            if task is None:
                raise ValueError(f"Task {task_id} not found")
            if task.get("chapter_id") != chapter_id:
                raise ValueError(f"Task {task_id} is not linked to chapter {chapter_id}")

            cursor.execute("SELECT final_path, status FROM ai_novel_chapter WHERE id = %s FOR UPDATE", (chapter_id,))
            chapter = cursor.fetchone()
            if chapter is None:
                raise ValueError(f"Chapter {chapter_id} not found")
            if _is_final_chapter(chapter.get("status"), chapter.get("final_path")):
                raise ValueError(f"Chapter {chapter_id} already has final content; refusing to overwrite draft state")

            cursor.execute(
                "UPDATE ai_novel_chapter SET draft_path = %s, word_count = %s, status = 'drafted' WHERE id = %s",
                (draft_path, word_count, chapter_id),
            )
            cursor.execute(
                "UPDATE ai_novel_task SET status = 'completed', finished_at = CURRENT_TIMESTAMP WHERE id = %s",
                (task_id,),
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def create_review_issue(
        self,
        project_id: int,
        chapter_id: int | None,
        task_id: int | None,
        issue_type: str,
        severity: int,
        title: str,
        detail: str,
        suggestion: str,
    ) -> None:
        execute(
            self.connection,
            "INSERT INTO ai_novel_review_issue "
            "(project_id, chapter_id, task_id, issue_type, severity, title, detail, suggestion, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open')",
            (project_id, chapter_id, task_id, issue_type, severity, title, detail, suggestion),
        )

    def create_review_issues(self, issues: list[dict[str, object]]) -> None:
        cursor = self.connection.cursor()
        try:
            for issue in issues:
                cursor.execute(
                    "INSERT INTO ai_novel_review_issue "
                    "(project_id, chapter_id, task_id, issue_type, severity, title, detail, suggestion, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open')",
                    (
                        issue["project_id"],
                        issue["chapter_id"],
                        issue["task_id"],
                        issue["issue_type"],
                        issue["severity"],
                        issue["title"],
                        issue["detail"],
                        issue["suggestion"],
                    ),
                )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()


def _is_final_chapter(status: object, final_path: object) -> bool:
    return bool(final_path) or str(status).lower() in {"final", "finalized", "completed", "published"}
