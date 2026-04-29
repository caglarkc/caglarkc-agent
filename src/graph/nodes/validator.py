from __future__ import annotations

import ast
import importlib.util
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


async def validator_node(state: dict) -> dict:
    settings = get_settings()
    project_root = settings.projects_root / state["project_name"]
    outputs = [item for values in state.get("worker_outputs", {}).values() for item in values]
    validation_issues: list[dict[str, str]] = []

    for relative_path in outputs:
        path = (project_root / relative_path).resolve()
        try:
            path.relative_to(project_root.resolve())
        except ValueError:
            validation_issues.append({"target_file": relative_path, "issue": "path outside project root"})
            continue

        if path.suffix != ".py":
            continue
        syntax_issue = await _syntax_check(path)
        if syntax_issue:
            validation_issues.append({"target_file": relative_path, "issue": syntax_issue})
            continue
        import_issues = await _import_check(path, project_root)
        for issue in import_issues:
            validation_issues.append({"target_file": relative_path, "issue": issue})

    updates = {
        "validation_issues": validation_issues,
        "revision_tasks": [
            {"target_file": issue["target_file"], "reason": issue["issue"]} for issue in validation_issues
        ],
        "messages": [*state.get("messages", []), "validator completed"],
    }
    async with StateTransaction(state["project_id"]) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted
    return updates
