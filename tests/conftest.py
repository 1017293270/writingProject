from dataclasses import dataclass, field

import pytest

from writing_project.models import Chapter, Entity, PlotThread, Project, Task, TimelineEvent


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

    def mark_task_exported(self, task_id: int, context_path: str) -> None:
        self.exported = {"task_id": task_id, "context_path": context_path}

    def update_chapter_draft(self, chapter_id: int, draft_path: str, word_count: int) -> None:
        self.chapter_update = {"chapter_id": chapter_id, "draft_path": draft_path, "word_count": word_count}

    def mark_task_completed(self, task_id: int) -> None:
        self.completed_task_id = task_id

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


@pytest.fixture
def fake_repository() -> FakeRepository:
    return FakeRepository()
