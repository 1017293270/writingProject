from fastapi.testclient import TestClient

from writing_project.web import create_app


def test_web_index_lists_projects(fake_repository_context):
    client = TestClient(create_app(fake_repository_context))

    response = client.get("/")

    assert response.status_code == 200
    assert "示例长篇小说" in response.text
    assert "Projects" in response.text
    assert "/projects/new" in response.text


def test_web_project_detail_lists_core_tables(fake_repository_context):
    client = TestClient(create_app(fake_repository_context))

    response = client.get("/projects/1")

    assert response.status_code == 200
    assert "雪夜入城" in response.text
    assert "写第一章" in response.text
    assert "玉牌线索断裂" in response.text
    assert "/tasks/9/export" in response.text
    assert "/projects/1/chapters/new" in response.text
    assert "/projects/1/import" in response.text
    assert "/chapters/2/create-task" in response.text


def test_web_task_detail_shows_bridge_paths(fake_repository_context):
    client = TestClient(create_app(fake_repository_context))

    response = client.get("/tasks/9")

    assert response.status_code == 200
    assert "E:/novels/demo/tasks/task-0009.md" in response.text
    assert "E:/novels/demo/context/context-0009.json" in response.text
    assert "E:/novels/demo/outputs/ch001.md" in response.text


def test_web_export_task_redirects_with_message(fake_repository_context, fake_repository, tmp_path):
    fake_repository.task = fake_repository.task.__class__(
        **{
            **fake_repository.task.__dict__,
            "instruction_path": str(tmp_path / "tasks" / "task.md"),
            "context_path": str(tmp_path / "context" / "context.json"),
        }
    )
    client = TestClient(create_app(fake_repository_context))

    response = client.post("/tasks/9/export", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/projects/1?message=")
    assert (tmp_path / "tasks" / "task.md").exists()
    assert (tmp_path / "context" / "context.json").exists()


def test_web_create_project_form_creates_project(fake_repository_context, fake_repository, tmp_path):
    client = TestClient(create_app(fake_repository_context))

    response = client.post(
        "/projects",
        data={
            "name": "新小说",
            "genre": "都市",
            "premise": "一句话故事",
            "root_dir": str(tmp_path / "new-novel"),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert fake_repository.created_projects[0]["name"] == "新小说"


def test_web_create_chapter_form_creates_chapter(fake_repository_context, fake_repository):
    client = TestClient(create_app(fake_repository_context))

    response = client.post(
        "/projects/1/chapters",
        data={"volume_no": "1", "chapter_no": "2", "title": "第二章", "outline": "继续推进。"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert fake_repository.created_chapters[0]["title"] == "第二章"


def test_web_import_markdown_file_creates_drafted_chapter(fake_repository_context, fake_repository, tmp_path):
    markdown = tmp_path / "ch001.md"
    markdown.write_text("# 第一章\n风雪压城。", encoding="utf-8")
    client = TestClient(create_app(fake_repository_context))

    response = client.post(
        "/projects/1/import",
        data={"mode": "file", "path": str(markdown), "volume_no": "1", "start_chapter_no": "1"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert fake_repository.created_chapters[0]["draft_path"] == str(markdown)


def test_web_create_task_for_chapter(fake_repository_context, fake_repository):
    client = TestClient(create_app(fake_repository_context))

    response = client.post("/chapters/2/create-task", follow_redirects=False)

    assert response.status_code == 303
    assert fake_repository.created_tasks[0]["task_type"] == "write_chapter"
