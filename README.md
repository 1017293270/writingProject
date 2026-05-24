# Writing Project

Local writing console for Codex-assisted long-form fiction.

## Setup

1. Create the MySQL `ai_novel_%` tables from the design SQL.
2. Copy `.env.example` to `.env` and fill in your MySQL credentials.
3. Install dependencies:

```powershell
python -m pip install -e ".[dev]"
```

## Commands

```powershell
writing-project projects
writing-project tasks --project-id 1
writing-project export-task 1
writing-project import-output 1
writing-project import-review 1 E:/ai辅助平台/novels/demo-novel/reviews/review-0001.json
```

## Manual Smoke Test

After creating the database tables and seed rows:

```powershell
copy .env.example .env
writing-project projects
writing-project tasks --project-id 1
writing-project export-task 1
```

Open the printed task Markdown file and ask Codex to execute it. After Codex writes the output file:

```powershell
writing-project import-output 1
```

For review issues, create a JSON report:

```json
{
  "issues": [
    {
      "issue_type": "continuity",
      "severity": 2,
      "title": "人物状态不一致",
      "detail": "角色上一章受伤，本章行动没有体现影响。",
      "suggestion": "补充行动受限或恢复原因。"
    }
  ]
}
```

Then run:

```powershell
writing-project import-review 1 E:/ai辅助平台/novels/demo-novel/reviews/review-0001.json
```
