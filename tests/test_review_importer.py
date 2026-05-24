import json

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
