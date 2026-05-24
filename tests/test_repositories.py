from writing_project.models import Chapter, Project, Task
from writing_project.repositories import NovelRepository, row_to_chapter, row_to_project, row_to_task


def test_row_to_project_maps_database_fields():
    project = row_to_project(
        {
            "id": 1,
            "name": "Demo",
            "genre": "玄幻",
            "premise": "Premise",
            "style_guide_path": "style.md",
            "root_dir": "E:/novel",
            "status": "active",
        }
    )

    assert project == Project(
        id=1,
        name="Demo",
        genre="玄幻",
        premise="Premise",
        style_guide_path="style.md",
        root_dir="E:/novel",
        status="active",
    )


def test_row_to_chapter_maps_nullable_paths():
    chapter = row_to_chapter(
        {
            "id": 2,
            "project_id": 1,
            "volume_no": 1,
            "chapter_no": 3,
            "title": "Title",
            "outline": None,
            "summary": None,
            "draft_path": None,
            "final_path": None,
            "status": "planned",
            "word_count": 0,
        }
    )

    assert chapter == Chapter(
        id=2,
        project_id=1,
        volume_no=1,
        chapter_no=3,
        title="Title",
        outline="",
        summary="",
        draft_path=None,
        final_path=None,
        status="planned",
        word_count=0,
    )


def test_row_to_task_maps_paths_and_priority():
    task = row_to_task(
        {
            "id": 9,
            "project_id": 1,
            "chapter_id": 2,
            "task_type": "write_chapter",
            "title": "Write",
            "instruction_path": "task.md",
            "context_path": "context.json",
            "output_path": "out.md",
            "status": "pending",
            "priority": 1,
        }
    )

    assert task == Task(
        id=9,
        project_id=1,
        chapter_id=2,
        task_type="write_chapter",
        title="Write",
        instruction_path="task.md",
        context_path="context.json",
        output_path="out.md",
        status="pending",
        priority=1,
    )


class RecordingCursor:
    def __init__(self, chapter_row=None, fail_on_task_update=False):
        self.chapter_row = chapter_row or {"final_path": None, "status": "planned"}
        self.fail_on_task_update = fail_on_task_update
        self.statements = []
        self.closed = False

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        if self.fail_on_task_update and sql.startswith("UPDATE ai_novel_task"):
            raise RuntimeError("task update failed")

    def fetchone(self):
        return self.chapter_row

    def close(self):
        self.closed = True


class RecordingConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_complete_task_output_updates_chapter_and_task_in_one_commit():
    cursor = RecordingCursor()
    connection = RecordingConnection(cursor)

    NovelRepository(connection).complete_task_output(9, 2, "out.md", 1200)

    assert len(cursor.statements) == 3
    assert cursor.statements[1][0].startswith("UPDATE ai_novel_chapter")
    assert cursor.statements[2][0].startswith("UPDATE ai_novel_task")
    assert connection.committed is True
    assert connection.rolled_back is False
    assert cursor.closed is True


def test_complete_task_output_refuses_final_chapter_and_rolls_back():
    cursor = RecordingCursor({"final_path": "final.md", "status": "final"})
    connection = RecordingConnection(cursor)

    try:
        NovelRepository(connection).complete_task_output(9, 2, "out.md", 1200)
    except ValueError as exc:
        assert "already has final content" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

    assert len(cursor.statements) == 1
    assert connection.committed is False
    assert connection.rolled_back is True


def test_complete_task_output_rolls_back_when_task_update_fails():
    cursor = RecordingCursor(fail_on_task_update=True)
    connection = RecordingConnection(cursor)

    try:
        NovelRepository(connection).complete_task_output(9, 2, "out.md", 1200)
    except RuntimeError as exc:
        assert "task update failed" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")

    assert connection.committed is False
    assert connection.rolled_back is True
