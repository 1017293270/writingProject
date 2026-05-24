from dataclasses import dataclass, field
from contextlib import contextmanager

import pytest

from writing_project.models import Chapter, Entity, PlotThread, Project, ReviewIssue, Task, TimelineEvent


@dataclass
class FakeRepository:
    project: Project = field(
        default_factory=lambda: Project(
            1,
            "示例长篇小说",
            "玄幻 / 权谋",
            "少年寻找自身来历。",
            "E:/novels/demo/world/style-guide.md",
            "E:/novels/demo",
            "active",
        )
    )
    chapter: Chapter = field(
        default_factory=lambda: Chapter(
            2,
            1,
            1,
            1,
            "雪夜入城",
            "主角抵达寒鸦城。",
            "前章摘要。",
            None,
            None,
            "planned",
            0,
        )
    )
    task: Task = field(
        default_factory=lambda: Task(
            9,
            1,
            2,
            "write_chapter",
            "写第一章",
            "E:/novels/demo/tasks/task-0009.md",
            "E:/novels/demo/context/context-0009.json",
            "E:/novels/demo/outputs/ch001.md",
            "pending",
            1,
        )
    )
    created_review_issues: list[dict] = field(default_factory=list)
    created_projects: list[dict] = field(default_factory=list)
    created_chapters: list[dict] = field(default_factory=list)
    created_tasks: list[dict] = field(default_factory=list)
    previous_summaries: list[str] = field(default_factory=lambda: ["前一章摘要。"])

    def get_task(self, task_id: int) -> Task:
        assert task_id == self.task.id
        return self.task

    def get_project(self, project_id: int) -> Project:
        assert project_id == self.project.id
        return self.project

    def list_projects(self) -> list[Project]:
        return [self.project]

    def get_chapter(self, chapter_id: int) -> Chapter:
        assert chapter_id == self.chapter.id
        return self.chapter

    def list_chapters(self, project_id: int) -> list[Chapter]:
        return [self.chapter]

    def list_tasks(self, project_id: int, status: str | None = None) -> list[Task]:
        if status and self.task.status != status:
            return []
        return [self.task]

    def list_entities(self, project_id: int) -> list[Entity]:
        return [
            Entity(
                1,
                project_id,
                "character",
                "沈砚",
                ["阿砚"],
                "男主。",
                "刚抵达边境城。",
                "E:/novels/demo/entities/characters/shen-yan.md",
                5,
            )
        ]

    def list_plot_threads(self, project_id: int) -> list[PlotThread]:
        return [
            PlotThread(
                1,
                project_id,
                "mystery",
                "残缺玉牌的来历",
                "玉牌与旧朝密令有关。",
                self.chapter.id,
                None,
                "open",
                "E:/novels/demo/plot-threads/jade-token.md",
            )
        ]

    def list_timeline(self, project_id: int, through_chapter_id: int | None = None) -> list[TimelineEvent]:
        return [
            TimelineEvent(
                1,
                project_id,
                self.chapter.id,
                "1.001",
                "沈砚雪夜入城",
                "沈砚抵达寒鸦城。",
                ["沈砚", "寒鸦城"],
                "planned",
            )
        ]

    def list_previous_chapter_summaries(
        self, project_id: int, volume_no: int, chapter_no: int, limit: int = 3
    ) -> list[str]:
        return self.previous_summaries

    def mark_task_exported(self, task_id: int, context_path: str) -> None:
        self.exported = {"task_id": task_id, "context_path": context_path}

    def update_chapter_draft(self, chapter_id: int, draft_path: str, word_count: int) -> None:
        self.chapter_update = {"chapter_id": chapter_id, "draft_path": draft_path, "word_count": word_count}

    def mark_task_completed(self, task_id: int) -> None:
        self.completed_task_id = task_id

    def complete_task_output(self, task_id: int, chapter_id: int, draft_path: str, word_count: int) -> None:
        self.update_chapter_draft(chapter_id, draft_path, word_count)
        self.mark_task_completed(task_id)

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
        self.created_review_issues.append(
            {
                "project_id": project_id,
                "chapter_id": chapter_id,
                "task_id": task_id,
                "issue_type": issue_type,
                "severity": severity,
                "title": title,
                "detail": detail,
                "suggestion": suggestion,
            }
        )

    def create_review_issues(self, issues: list[dict[str, object]]) -> None:
        self.created_review_issues.extend(issues)

    def list_review_issues(self, project_id: int, status: str | None = None) -> list[ReviewIssue]:
        return [
            ReviewIssue(
                1,
                project_id,
                self.chapter.id,
                self.task.id,
                "continuity",
                2,
                "玉牌线索断裂",
                "缺少呼应。",
                "补一处反应。",
                "open",
            )
        ]

    def create_project(
        self, name: str, genre: str, premise: str, style_guide_path: str, root_dir: str, status: str = "active"
    ) -> int:
        self.created_projects.append(
            {
                "name": name,
                "genre": genre,
                "premise": premise,
                "style_guide_path": style_guide_path,
                "root_dir": root_dir,
                "status": status,
            }
        )
        return 100 + len(self.created_projects)

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
    ) -> int:
        self.created_chapters.append(
            {
                "project_id": project_id,
                "volume_no": volume_no,
                "chapter_no": chapter_no,
                "title": title,
                "outline": outline,
                "summary": summary,
                "draft_path": draft_path,
                "final_path": final_path,
                "status": status,
                "word_count": word_count,
            }
        )
        return 201 + len(self.created_chapters)

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
    ) -> int:
        self.created_tasks.append(
            {
                "project_id": project_id,
                "chapter_id": chapter_id,
                "task_type": task_type,
                "title": title,
                "instruction_path": instruction_path,
                "context_path": context_path,
                "output_path": output_path,
                "status": status,
                "priority": priority,
            }
        )
        return 302 + len(self.created_tasks)


@pytest.fixture
def fake_repository() -> FakeRepository:
    return FakeRepository()


@pytest.fixture
def fake_repository_context(fake_repository):
    @contextmanager
    def factory():
        yield fake_repository

    return factory
