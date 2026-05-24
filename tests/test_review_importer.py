import json

import pytest

from writing_project.review_importer import import_review_issues


def test_import_review_issues_creates_database_rows(fake_repository, tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(
        json.dumps(
            {
                "issues": [
                    {
                        "issue_type": "continuity",
                        "severity": 2,
                        "title": "玉牌线索断裂",
                        "detail": "本章出现玉牌但没有呼应通缉令。",
                        "suggestion": "补一处沈砚看到图案后的反应。",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    count = import_review_issues(fake_repository, task_id=9, review_path=review_file)

    assert count == 1
    assert fake_repository.created_review_issues[0]["title"] == "玉牌线索断裂"
    assert fake_repository.created_review_issues[0]["chapter_id"] == 2


def test_import_review_issues_validates_before_writing(fake_repository, tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(
        json.dumps(
            {
                "issues": [
                    {
                        "issue_type": "continuity",
                        "severity": 2,
                        "title": "有效问题",
                    },
                    {
                        "severity": 3,
                        "title": "缺少类型",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing 'issue_type'"):
        import_review_issues(fake_repository, task_id=9, review_path=review_file)

    assert fake_repository.created_review_issues == []


def test_import_review_issues_requires_object_root(fake_repository, tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps([]), encoding="utf-8")

    with pytest.raises(ValueError, match="root must be an object"):
        import_review_issues(fake_repository, task_id=9, review_path=review_file)


def test_import_review_issues_requires_issues_array(fake_repository, tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps({}), encoding="utf-8")

    with pytest.raises(ValueError, match="must contain an 'issues' array"):
        import_review_issues(fake_repository, task_id=9, review_path=review_file)

    assert fake_repository.created_review_issues == []
