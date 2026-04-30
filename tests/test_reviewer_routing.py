from __future__ import annotations

from src.graph.nodes.reviewer import _targets_for_issue


def _queue(paths: list[str]) -> list[dict]:
    return [{"assignment": {"target_file": path}} for path in paths]


def test_project_level_final_review_issue_routes_to_mentioned_files() -> None:
    issue = {
        "target_file": "__project__",
        "message": "script.js references menu-button but index.html does not define it.",
    }

    assert _targets_for_issue(issue, _queue(["index.html", "styles.css", "script.js"])) == ["index.html", "script.js"]


def test_project_level_unmapped_issue_routes_to_frontend_files() -> None:
    issue = {"target_file": "__project__", "message": "frontend files are inconsistent"}

    assert _targets_for_issue(issue, _queue(["index.html", "styles.css", "script.js", "README.md"])) == [
        "index.html",
        "styles.css",
        "script.js",
    ]
