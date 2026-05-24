from writing_project.files import count_words, read_json, write_json, write_text


def test_write_json_creates_parent_directories(tmp_path):
    path = tmp_path / "context" / "task.json"

    write_json(path, {"title": "雪夜入城"})

    assert read_json(path) == {"title": "雪夜入城"}


def test_write_text_creates_parent_directories(tmp_path):
    path = tmp_path / "outputs" / "chapter.md"

    write_text(path, "# 第一章\n风雪压城。")

    assert path.read_text(encoding="utf-8") == "# 第一章\n风雪压城。"


def test_count_words_handles_cjk_and_latin():
    assert count_words("风雪压城 Shen Yan arrived.") == 7
