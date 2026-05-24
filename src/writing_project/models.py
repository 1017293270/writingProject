from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    genre: str
    premise: str
    style_guide_path: str | None
    root_dir: str
    status: str


@dataclass(frozen=True)
class Chapter:
    id: int
    project_id: int
    volume_no: int
    chapter_no: int
    title: str
    outline: str
    summary: str
    draft_path: str | None
    final_path: str | None
    status: str
    word_count: int


@dataclass(frozen=True)
class Entity:
    id: int
    project_id: int
    entity_type: str
    name: str
    alias: object | None
    description: str
    current_state: str
    detail_path: str | None
    importance: int


@dataclass(frozen=True)
class PlotThread:
    id: int
    project_id: int
    thread_type: str
    title: str
    description: str
    setup_chapter_id: int | None
    payoff_chapter_id: int | None
    status: str
    notes_path: str | None


@dataclass(frozen=True)
class TimelineEvent:
    id: int
    project_id: int
    chapter_id: int | None
    event_order: str
    title: str
    description: str
    involved_entities: object | None
    certainty: str


@dataclass(frozen=True)
class Task:
    id: int
    project_id: int
    chapter_id: int | None
    task_type: str
    title: str
    instruction_path: str
    context_path: str | None
    output_path: str | None
    status: str
    priority: int
