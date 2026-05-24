from writing_project.models import Chapter, Project, Task
from writing_project.repositories import row_to_chapter, row_to_project, row_to_task


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
