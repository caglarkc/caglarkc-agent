from __future__ import annotations

import ast
import importlib.util
import json
import py_compile
from pathlib import Path

import aiofiles
import aiofiles.ospath

from src.config.settings import get_settings
from src.core.state_transaction import StateTransaction


async def _syntax_check(path: Path) -> str | None:
    try:
        await __import__("asyncio").to_thread(py_compile.compile, str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        return str(exc)
    return None


async def _import_check(path: Path, project_root: Path) -> list[str]:
    issues: list[str] = []
    async with aiofiles.open(path, "r", encoding="utf-8") as handle:
        content = await handle.read()
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module.split(".")[0]]
        else:
            continue
        for module_name in modules:
            local_candidate = project_root / f"{module_name}.py"
            if await aiofiles.ospath.exists(local_candidate):
                continue
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                issues.append(f"missing import: {module_name}")
    return issues


def _policy_issues(relative_path: str, content: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    lowered = content.lower()
    if ".." in relative_path.split("/"):
        issues.append(
            {
                "code": "path_traversal",
                "severity": "error",
                "target_file": relative_path,
                "message": "path traversal is not allowed",
            }
        )
    if "ignore previous instructions" in lowered or "prompt override" in lowered:
        issues.append(
            {
                "code": "prompt_override",
                "severity": "error",
                "target_file": relative_path,
                "message": "prompt override content detected",
            }
        )
    if "/etc/" in content or "~/" in content:
        issues.append(
            {
                "code": "forbidden_path_override",
                "severity": "error",
                "target_file": relative_path,
                "message": "forbidden path override detected",
            }
        )
    return issues


def _issue(target_file: str, code: str, message: str, severity: str = "error") -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "target_file": target_file,
        "message": message,
    }


async def validator_node(state: dict) -> dict:
    settings = get_settings()
    project_root = settings.projects_root / state["project_name"]
    outputs = sorted({item for values in state.get("worker_outputs", {}).values() for item in values})
    validation_issues: list[dict[str, str]] = []

    for relative_path in outputs:
        if ".." in Path(relative_path).parts:
            validation_issues.append(_issue(relative_path, "path_traversal", "path traversal is not allowed"))
            continue
        path = (project_root / relative_path).resolve()
        try:
            path.relative_to(project_root.resolve())
        except ValueError:
            validation_issues.append(_issue(relative_path, "path_outside_root", "path outside project root"))
            continue
        if not await aiofiles.ospath.exists(path):
            validation_issues.append(_issue(relative_path, "missing_file", "generated file is missing"))
            continue

        async with aiofiles.open(path, "r", encoding="utf-8") as handle:
            content = await handle.read()
        validation_issues.extend(_policy_issues(relative_path, content))

        if path.suffix != ".py":
            if path.suffix == ".json":
                try:
                    json.loads(content)
                except json.JSONDecodeError as exc:
                    validation_issues.append(_issue(relative_path, "json_parse_error", str(exc)))
            continue
        syntax_issue = await _syntax_check(path)
        if syntax_issue:
            validation_issues.append(_issue(relative_path, "python_syntax_error", syntax_issue))
            continue
        import_issues = await _import_check(path, project_root)
        for issue in import_issues:
            validation_issues.append(_issue(relative_path, "missing_import", issue))

    updates = {
        "validation_issues": validation_issues,
        "revision_tasks": [
            {"target_file": issue["target_file"], "reason": issue["message"], "code": issue["code"]}
            for issue in validation_issues
        ],
        "messages": ["validator completed"],
    }
    async with StateTransaction(state["project_id"]) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted
    return updates
