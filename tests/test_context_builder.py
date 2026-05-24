from writing_project.context_builder import build_context


def test_build_context_includes_project_chapter_entities_and_output(fake_repository):
    context = build_context(fake_repository, task_id=9)

    assert context["project"]["name"] == "示例长篇小说"
    assert context["chapter"]["title"] == "雪夜入城"
    assert context["entities"][0]["name"] == "沈砚"
    assert context["plot_threads"][0]["title"] == "残缺玉牌的来历"
    assert context["timeline"][0]["title"] == "沈砚雪夜入城"
    assert context["previous_summary"] == "前一章摘要。"
    assert context["output"]["path"] == "E:/novels/demo/outputs/ch001.md"
    assert context["output"]["format"] == "markdown"
