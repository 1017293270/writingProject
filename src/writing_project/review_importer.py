from __future__ import annotations

from pathlib import Path
from typing import Protocol

from writing_project.files import read_json
from writing_project.models import Task


class ReviewRepository(Protocol):
    def get_task(self, task_id: int) -> Task: ...
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
    ) -> None: ...


def import_review_issues(repository: ReviewRepository, task_id: int, review_path: str | Path) -> int:
    task = repository.get_task(task_id)
    payload = read_json(review_path)
    if not isinstance(payload, dict):
        raise ValueError("Review JSON root must be an object")

    if "issues" not in payload:
        raise ValueError("Review JSON must contain an 'issues' array")
    issues = payload["issues"]
    if not isinstance(issues, list):
        raise ValueError("Review JSON must contain an 'issues' array")

    prepared = [_prepare_issue(task, issue) for issue in issues]
    if hasattr(repository, "create_review_issues"):
        repository.create_review_issues(prepared)
    else:
        for issue in prepared:
            repository.create_review_issue(
                project_id=int(issue["project_id"]),
                chapter_id=issue["chapter_id"],
                task_id=int(issue["task_id"]),
                issue_type=str(issue["issue_type"]),
                severity=int(issue["severity"]),
                title=str(issue["title"]),
                detail=str(issue["detail"]),
                suggestion=str(issue["suggestion"]),
            )
    return len(prepared)


def _prepare_issue(task: Task, issue: object) -> dict[str, object]:
    if not isinstance(issue, dict):
        raise ValueError("Each review issue must be an object")
    if "issue_type" not in issue:
        raise ValueError("Review issue is missing 'issue_type'")
    if "title" not in issue:
        raise ValueError("Review issue is missing 'title'")

    return {
        "project_id": task.project_id,
        "chapter_id": task.chapter_id,
        "task_id": task.id,
        "issue_type": str(issue["issue_type"]),
        "severity": int(issue.get("severity", 3)),
        "title": str(issue["title"]),
        "detail": str(issue.get("detail", "")),
        "suggestion": str(issue.get("suggestion", "")),
    }
