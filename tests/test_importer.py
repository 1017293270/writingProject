import pytest

from writing_project.importer import import_task_output


def test_import_task_output_updates_chapter_and_task(fake_repository, tmp_path):
    output = tmp_path / "ch001.md"
    output.write_text("# 雪夜入城\n风雪压城。", encoding="utf-8")
    fake_repository.task = fake_repository.task.__class__(**{**fake_repository.task.__dict__, "output_path": str(output)})

    result = import_task_output(fake_repository, 9)

    assert result["word_count"] == 8
    assert fake_repository.chapter_update == {"chapter_id": 2, "draft_path": str(output), "word_count": 8}
    assert fake_repository.completed_task_id == 9


def test_import_task_output_fails_when_output_missing(fake_repository, tmp_path):
    fake_repository.task = fake_repository.task.__class__(
        **{**fake_repository.task.__dict__, "output_path": str(tmp_path / "missing.md")}
    )

    with pytest.raises(FileNotFoundError):
        import_task_output(fake_repository, 9)
