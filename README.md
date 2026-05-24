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
