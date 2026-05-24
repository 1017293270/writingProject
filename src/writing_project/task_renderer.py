from __future__ import annotations

from pathlib import Path
from typing import Any

from writing_project.context_builder import ContextRepository, build_context
from writing_project.files import write_json, write_text
from writing_project.models import Task


def render_task_markdown(task: Task, context: dict[str, Any]) -> str:
    chapter = context["chapter"]
    output_path = context["output"]["path"]
    context_path = task.context_path or ""
    return f"""# {task.title}

任务类型：`{task.task_type}`

## 输入文件

- 上下文包：`{context_path}`
- 风格指南：`{context["style"].get("style_guide_path") or "未设置"}`

## 写作目标

- 项目：{context["project"]["name"]}
- 卷号：{chapter["volume_no"]}
- 章节号：{chapter["chapter_no"]}
- 标题：{chapter["title"]}
- 章纲：{chapter["outline"]}

## 输出要求

- 输出路径：`{output_path}`
- 输出格式：Markdown
- 正文应直接写入输出路径。
- 不要改写或删除上下文包文件。
- 不要覆盖最终稿文件。

## 连贯性检查

- 保持人物动机和当前状态一致。
- 遵守时间线顺序。
- 推进或保留上下文包中列出的伏笔。
- 不要引入未解释的关键设定变化。

## 验收标准

- 章节内容与章纲一致。
- 主要角色行为符合上下文中的当前状态。
- 伏笔没有被遗忘或错误回收。
- 输出文件存在且内容为 UTF-8 Markdown。
"""


def export_task_files(repository: ContextRepository, task_id: int) -> tuple[Path, Path]:
    task = repository.get_task(task_id)
    if task.context_path is None:
        raise ValueError(f"Task {task_id} has no context_path")

    context = build_context(repository, task_id)
    context_path = write_json(task.context_path, context)
    task_markdown = render_task_markdown(task, context)
    instruction_path = write_text(task.instruction_path, task_markdown)

    if hasattr(repository, "mark_task_exported"):
        repository.mark_task_exported(task.id, str(context_path))

    return instruction_path, context_path
