from pathlib import Path

from writing_project.project_actions import (
    create_chapter,
    create_project,
    create_write_task,
    import_markdown_directory,
    import_markdown_file,
)


def test_create_project_creates_workspace_directories(fake_repository, tmp_path):
    root_dir = tmp_path / "new-novel"

    project_id = create_project(fake_repository, "新小说", "都市", "一句话故事", root_dir)

    assert project_id == 101
    assert (root_dir / "world").is_dir()
    assert (root_dir / "entities" / "characters").is_dir()
    assert (root_dir / "chapters").is_dir()
    assert fake_repository.created_projects[0]["name"] == "新小说"
    assert fake_repository.created_projects[0]["style_guide_path"] == str(root_dir / "world" / "style-guide.md")


def test_create_chapter_inserts_planned_chapter(fake_repository):
    chapter_id = create_chapter(fake_repository, 1, 2, 8, "雨夜归途", "主角回城。")

    assert chapter_id == 202
    assert fake_repository.created_chapters[0]["chapter_no"] == 8
    assert fake_repository.created_chapters[0]["status"] == "planned"


def test_import_markdown_file_creates_drafted_chapter(fake_repository, tmp_path):
    markdown = tmp_path / "chapter-001.md"
    markdown.write_text("# 第一章\n风雪压城。", encoding="utf-8")

    chapter_id = import_markdown_file(fake_repository, 1, markdown, 1, 1)

    assert chapter_id == 202
    created = fake_repository.created_chapters[0]
    assert created["title"] == "chapter-001"
    assert created["draft_path"] == str(markdown)
    assert created["word_count"] == 7
    assert created["status"] == "drafted"


def test_import_markdown_directory_imports_sorted_markdown_files(fake_repository, tmp_path):
    (tmp_path / "02.md").write_text("第二章", encoding="utf-8")
    (tmp_path / "01.md").write_text("第一章", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("nope", encoding="utf-8")

    imported = import_markdown_directory(fake_repository, 1, tmp_path, volume_no=1, start_chapter_no=3)

    assert imported == [202, 203]
    assert [row["chapter_no"] for row in fake_repository.created_chapters] == [3, 4]
    assert [Path(row["draft_path"]).name for row in fake_repository.created_chapters] == ["01.md", "02.md"]


def test_create_write_task_uses_project_root_and_chapter_numbers(fake_repository):
    task_id = create_write_task(fake_repository, 2)

    assert task_id == 303
    created = fake_repository.created_tasks[0]
    assert created["task_type"] == "write_chapter"
    assert "task-0002-write-chapter-001.md" in created["instruction_path"]
    assert "context-0002-write-chapter-001.json" in created["context_path"]
    assert "ch001-draft.md" in created["output_path"]
