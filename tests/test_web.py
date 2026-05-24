from fastapi.testclient import TestClient

from writing_project.web import create_app


def test_web_index_lists_projects(fake_repository_context):
    client = TestClient(create_app(fake_repository_context))

    response = client.get("/")

    assert response.status_code == 200
    assert "示例长篇小说" in response.text
    assert "Projects" in response.text


def test_web_project_detail_lists_core_tables(fake_repository_context):
    client = TestClient(create_app(fake_repository_context))

    response = client.get("/projects/1")

    assert response.status_code == 200
    assert "雪夜入城" in response.text
    assert "写第一章" in response.text
    assert "玉牌线索断裂" in response.text
    assert "/tasks/9/export" in response.text


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
