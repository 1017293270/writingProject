from writing_project.context_builder import build_context
from writing_project.task_renderer import render_task_markdown


def test_render_task_markdown_contains_paths_and_acceptance(fake_repository):
    context = build_context(fake_repository, 9)
    markdown = render_task_markdown(fake_repository.task, context)

    assert "# 写第一章" in markdown
    assert "任务类型：`write_chapter`" in markdown
    assert "E:/novels/demo/context/context-0009.json" in markdown
    assert "E:/novels/demo/outputs/ch001.md" in markdown
    assert "不要改写或删除上下文包文件" in markdown
