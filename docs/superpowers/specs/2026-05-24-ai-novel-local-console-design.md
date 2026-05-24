# AI 小说本地写作中控台设计

## 背景

本项目要解决 AI 长篇小说写作中常见的质量问题：行文不连贯、剧情割裂、人物状态漂移、伏笔遗忘、设定前后冲突。第一版面向个人本地使用，不做多用户 SaaS，也不依赖外部模型 API。

用户使用 Codex 写作时，平台通过 MySQL 和本地文件提供稳定上下文。MySQL 保存结构化记忆和任务状态，Markdown/JSON 保存 Codex 可直接读取和写入的长文本材料。这样即使 Codex 不能外接 API，也能通过读取数据库查询结果和本地文件完成写作任务。

## 目标

第一版目标是跑通一条可重复的文件桥接工作流：

1. 在 MySQL 中维护项目、章节、设定、伏笔、时间线和任务。
2. 从待执行任务生成 Codex 可读的任务说明和上下文包。
3. Codex 读取本地文件，完成章节写作、审查或修订。
4. 平台导入 Codex 输出，更新章节、任务和审查状态。
5. 每次写作都能明确使用哪些设定、前文摘要、角色状态和伏笔约束。

## 非目标

第一版不实现以下内容：

- 多用户账号、权限、计费或在线协作。
- 直接调用外部大模型 API。
- 自动让 Codex 在后台连续执行任务。
- 复杂富文本编辑器。
- 完整出版排版、投稿格式导出。

这些能力可以在文件桥接流程稳定后继续扩展。

## 技术前提

- 本机已有可用 MySQL 8。
- 已创建 `ai_novel_%` 系列表。
- 小说正文、设定长文、任务说明和审查报告以本地文件形式保存。
- Codex 可以读取项目目录中的 Markdown/JSON 文件，并按任务要求写入输出文件。

## 数据模型

MySQL 负责保存结构化状态：

- `ai_novel_project`：项目基础信息、根目录、风格指南路径。
- `ai_novel_chapter`：卷号、章节号、章纲、摘要、正文路径、状态、字数。
- `ai_novel_entity`：角色、地点、势力、道具、概念等实体。
- `ai_novel_plot_thread`：主线、支线、伏笔、悬念和回收状态。
- `ai_novel_timeline_event`：按顺序记录剧情事件。
- `ai_novel_task`：写章、审查、修订等任务队列。
- `ai_novel_review_issue`：写后审查发现的问题和修订建议。

长文本不强塞进数据库。数据库保存路径、摘要、状态和关联关系，正文内容放在 Markdown/JSON 文件中。

## 文件结构

每个小说项目使用独立目录：

```text
novels/<project-slug>/
  world/
    style-guide.md
    world-bible.md
  entities/
    characters/
    locations/
    factions/
    items/
  chapters/
    v01/
      ch001-draft.md
      ch001-final.md
  tasks/
    task-0001-write-chapter-001.md
  context/
    context-0001-write-chapter-001.json
  outputs/
    ch001-draft.md
  reviews/
    review-0001-chapter-001.md
```

路径由 MySQL 记录，文件内容由平台和 Codex 共同读写。

## 核心工作流

### 1. 创建写作任务

用户在平台中选择项目和章节，创建 `write_chapter` 任务。平台写入 `ai_novel_task`，并生成：

- `tasks/task-xxxx.md`：自然语言任务说明。
- `context/context-xxxx.json`：结构化上下文包。

任务说明面向 Codex 阅读，包含写作目标、输出路径、禁止事项和验收标准。上下文包包含当前章节信息、相关角色、前文摘要、伏笔、时间线和文风约束。

### 2. Codex 执行任务

用户让 Codex 读取任务说明和上下文包。Codex 不需要访问外部 API，只需要：

- 读取 `task.md`。
- 读取 `context.json`。
- 必要时读取相关 Markdown 设定文件。
- 将章节草稿写入任务指定的输出路径。

Codex 输出应保持为 Markdown，方便后续 diff、版本管理和人工编辑。

### 3. 导入写作结果

平台读取任务的 `output_path`，计算字数，更新：

- `ai_novel_chapter.draft_path`
- `ai_novel_chapter.word_count`
- `ai_novel_chapter.status`
- `ai_novel_task.status`
- `ai_novel_task.finished_at`

导入时不覆盖已有最终稿。若同一章节多次生成草稿，应保留历史文件或使用带时间戳的输出路径。

### 4. 写后审查

审查可以作为单独 `review_chapter` 任务执行。审查重点包括：

- 人物动机是否连续。
- 人物状态是否与前文一致。
- 时间线是否冲突。
- 伏笔是否推进或遗忘。
- 本章是否偏离章纲。
- 文风是否明显漂移。

审查结果写入 Markdown 报告，结构化问题写入 `ai_novel_review_issue`。

### 5. 修订任务

当存在未解决审查问题时，平台可以创建 `revise_chapter` 任务。修订任务上下文应包含原章草稿、审查问题、必须保留的剧情点和输出路径。

## 上下文包格式

`context.json` 第一版采用稳定、可读的结构：

```json
{
  "project": {
    "id": 1,
    "name": "示例长篇小说",
    "genre": "玄幻 / 权谋",
    "premise": "一个被边缘化的少年在王朝与宗门夹缝中寻找自身来历。"
  },
  "chapter": {
    "id": 1,
    "volume_no": 1,
    "chapter_no": 1,
    "title": "雪夜入城",
    "outline": "主角在雪夜抵达边境城，发现通缉令上的图案与随身玉牌相同。",
    "status": "planned"
  },
  "style": {
    "style_guide_path": "E:/ai辅助平台/novels/demo-novel/world/style-guide.md",
    "rules": []
  },
  "entities": [],
  "plot_threads": [],
  "timeline": [],
  "previous_summary": "",
  "constraints": [],
  "output": {
    "path": "E:/ai辅助平台/novels/demo-novel/outputs/ch001-draft.md",
    "format": "markdown"
  }
}
```

字段可以逐步扩展，但第一版生成器必须保持向后兼容：新增字段不破坏旧任务。

## 平台界面

第一版界面以效率为主，不做复杂视觉包装：

- 项目列表：查看项目、根目录、状态。
- 章节列表：查看卷号、章节号、标题、状态、字数。
- 设定库：维护角色、地点、势力、道具、伏笔和时间线。
- 任务队列：查看待执行、进行中、已完成、失败任务。
- 任务详情：展示任务文件路径、上下文文件路径、输出路径和导入状态。
- 审查问题：查看问题类型、严重度、建议和解决状态。

## 错误处理

平台应明确处理以下错误：

- MySQL 连接失败：提示检查数据库服务、账号、库名和权限。
- 文件路径不存在：提示创建目录或重新生成任务文件。
- 输出文件不存在：导入前阻止状态更新。
- JSON 解析失败：提示上下文包损坏并允许重新生成。
- 外键引用缺失：阻止创建无项目或无章节的任务。
- 重复导入：保留已有内容，不静默覆盖。

## 测试策略

第一版至少验证以下场景：

- 能连接 MySQL 并读取 `ai_novel_project`。
- 能创建写章任务并生成 `task.md`、`context.json`。
- `context.json` 是合法 JSON，且包含章节和输出路径。
- 当输出 Markdown 存在时，导入器能更新任务和章节状态。
- 当输出 Markdown 不存在时，导入器不会误标记任务完成。
- 审查问题可以写入 `ai_novel_review_issue` 并关联章节和任务。

## 后续扩展

稳定后可以继续加入：

- 本地 Runner，自动扫描 pending 任务并辅助导入。
- 更细的实体关系图和章节级出场记录。
- 章节版本表或文件版本索引。
- Web UI 的可视化时间线、伏笔追踪和冲突报告。
- 外部模型 API 适配层，但不改变 MySQL + 文件桥接核心协议。

## 设计结论

第一版采用 MySQL + Markdown/JSON 文件桥接架构。它把长篇小说写作拆成可记录、可审查、可重复执行的任务链路，让 Codex 在没有外部 API 的情况下，仍然能够通过读取本地数据库衍生材料和项目文件完成高一致性的写作。
