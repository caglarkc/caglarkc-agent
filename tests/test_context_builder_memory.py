from __future__ import annotations

from pathlib import Path

import pytest

from src.config.settings import get_settings
from src.core.context_builder import ContextBuilder


@pytest.mark.asyncio
async def test_planner_memory_slice_strips_leading_html_comment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PROJECTS_ROOT", str(tmp_path / "projects"))
    get_settings.cache_clear()
    mem = tmp_path / "projects" / "P1" / ".meta" / "memory"
    mem.mkdir(parents=True, parents=True)
    (mem / "planner_memory.md").write_text("<!-- consolidated_at: x -->\n\n# Title\n\nbody", encoding="utf-8")

    builder = ContextBuilder()
    text = await builder._load_planner_memory_slice("P1")

    assert "<!--" not in text
    assert "Title" in text
    assert "body" in text
