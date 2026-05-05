from __future__ import annotations

from pathlib import Path

from src.config.settings import get_settings


def project_root_for_name(project_name: str) -> Path:
    settings = get_settings()
    return settings.projects_root / project_name


def memory_root_for_project(project_name: str) -> Path:
    settings = get_settings()
    rel = Path(settings.memory_relative_dir)
    return project_root_for_name(project_name) / rel


def consolidate_lock_path(project_name: str) -> Path:
    return memory_root_for_project(project_name) / ".consolidate-lock"


def sprint_snapshots_dir(project_name: str) -> Path:
    return project_root_for_name(project_name) / ".meta" / "sprints"


def planner_memory_path(project_name: str) -> Path:
    settings = get_settings()
    return memory_root_for_project(project_name) / settings.memory_planner_summary_file


def extracts_dir(project_name: str) -> Path:
    return memory_root_for_project(project_name) / "extracts"


def is_within_memory_root(project_name: str, candidate: Path) -> bool:
    root = memory_root_for_project(project_name).resolve()
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    return resolved == root or root in resolved.parents

