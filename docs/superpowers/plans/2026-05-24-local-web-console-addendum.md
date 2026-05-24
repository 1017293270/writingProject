# Local Web Console Addendum

## Goal

Add a local browser UI so the writing console can be used without memorizing CLI commands.

## Scope

- Add `writing-project web` to start a local server at `http://127.0.0.1:8000`.
- Show project list, project detail, chapters, task queue, and review issues.
- Let users export task files and import Codex output from buttons.
- Keep all database and file operations routed through the existing repository and service functions.

## Non-goals

- No login, multi-user permissions, external AI API calls, rich text editor, or frontend build pipeline.
- No direct chapter editing in the first Web UI pass.

## Implementation Notes

- Use FastAPI with server-rendered HTML strings for the first pass.
- Use restrained dashboard styling for scanability.
- Keep route handlers small and testable through injected repository contexts.
