from __future__ import annotations

import asyncio
import re
from pathlib import Path
import shutil
import sys

import aiofiles
import aiofiles.ospath

from src.config.settings import get_settings
from src.core.state_transaction import StateTransaction


MAX_OUTPUT_CHARS = 4_000
COMMAND_TIMEOUT_SECONDS = 20.0


def _clip(value: str, *, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}... [truncated]"


async def _run_command(project_root: Path, args: list[str], *, timeout: float = COMMAND_TIMEOUT_SECONDS) -> dict:
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        return {
            "command": args,
            "exit_code": process.returncode,
            "stdout": _clip(stdout),
            "stderr": _clip(stderr),
            "timed_out": False,
        }
    except asyncio.TimeoutError:
        return {
            "command": args,
            "exit_code": 124,
            "stdout": "",
            "stderr": f"command timed out after {timeout:.0f}s",
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "command": args,
            "exit_code": 127,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }


async def _read_text(path: Path) -> str:
    async with aiofiles.open(path, "r", encoding="utf-8") as handle:
        return await handle.read()


async def _check_static_site(project_root: Path, outputs: list[str]) -> list[dict]:
    results: list[dict] = []
    output_set = set(outputs)
    html_files = [path for path in outputs if path.endswith(".html")]
    css_files = [path for path in outputs if path.endswith(".css")]
    js_files = [path for path in outputs if path.endswith(".js")]

    for html_file in html_files:
        path = project_root / html_file
        content = await _read_text(path)
        issues: list[str] = []
        if "<html" not in content.lower():
            issues.append("missing <html> root")
        if "<body" not in content.lower():
            issues.append("missing <body> section")
        closing_index = content.lower().rfind("</html>")
        if closing_index >= 0 and content[closing_index + len("</html>") :].strip():
            issues.append(f"{html_file} has trailing content after </html>")
        for linked in css_files + js_files:
            if linked not in output_set:
                continue
            if Path(linked).name not in content and linked not in content:
                issues.append(f"{linked} is generated but not linked from {html_file}")
        results.append(
            {
                "target_file": html_file,
                "check": "static_html_structure",
                "exit_code": 1 if issues else 0,
                "stdout": "html structure ok" if not issues else "",
                "stderr": "; ".join(issues),
            }
        )

    for css_file in css_files:
        content = await _read_text(project_root / css_file)
        open_count = content.count("{")
        close_count = content.count("}")
        ok = open_count == close_count and open_count > 0
        results.append(
            {
                "target_file": css_file,
                "check": "css_brace_balance",
                "exit_code": 0 if ok else 1,
                "stdout": "css brace balance ok" if ok else "",
                "stderr": "" if ok else "CSS braces are unbalanced or stylesheet is empty",
            }
        )

    if js_files and shutil.which("node"):
        for js_file in js_files:
            command_result = await _run_command(project_root, ["node", "--check", js_file])
            command_result.update({"target_file": js_file, "check": "node_syntax"})
            results.append(command_result)
    elif js_files:
        for js_file in js_files:
            content = await _read_text(project_root / js_file)
            ok = content.count("(") == content.count(")") and content.count("{") == content.count("}")
            results.append(
                {
                    "target_file": js_file,
                    "check": "basic_js_balance",
                    "exit_code": 0 if ok else 1,
                    "stdout": "basic js balance ok" if ok else "",
                    "stderr": "" if ok else "JavaScript delimiters look unbalanced",
                }
            )

    results.extend(await _check_dom_consistency(project_root, html_files, css_files, js_files))
    return results


async def _check_dom_consistency(project_root: Path, html_files: list[str], css_files: list[str], js_files: list[str]) -> list[dict]:
    if not html_files:
        return []
    html_content = "\n".join([await _read_text(project_root / html_file) for html_file in html_files])
    html_ids = set(re.findall(r"""\bid\s*=\s*["']([^"']+)["']""", html_content))
    html_classes = set()
    for class_value in re.findall(r"""\bclass\s*=\s*["']([^"']+)["']""", html_content):
        html_classes.update(item for item in class_value.split() if item)
    issues: list[str] = []
    issue_targets: set[str] = set()

    for js_file in js_files:
        js_content = await _read_text(project_root / js_file)
        for element_id in re.findall(r"""getElementById\s*\(\s*["']([^"']+)["']\s*\)""", js_content):
            if element_id not in html_ids:
                issues.append(f"{js_file} references missing HTML id #{element_id}")
                issue_targets.update({js_file, html_files[0]})
        for selector in re.findall(r"""querySelector(?:All)?\s*\(\s*["']([^"']+)["']\s*\)""", js_content):
            selector_ids = re.findall(r"#([A-Za-z_][\w\-]*)", selector)
            selector_classes = re.findall(r"\.([A-Za-z_][\w\-]*)", selector)
            missing_ids = [element_id for element_id in selector_ids if element_id not in html_ids]
            missing_classes = [class_name for class_name in selector_classes if class_name not in html_classes]
            if missing_ids:
                issues.append(f"{js_file} references missing HTML selector id(s) {', '.join('#' + item for item in missing_ids)} in selector {selector}")
                issue_targets.update({js_file, html_files[0]})
            if missing_classes:
                issues.append(f"{js_file} references missing HTML selector class(es) {', '.join('.' + item for item in missing_classes)} in selector {selector}")
                issue_targets.update({js_file, html_files[0]})
            if " form" in selector and "<form" not in html_content.lower():
                issues.append(f"{js_file} references selector {selector}, but no <form> element exists in HTML")
                issue_targets.update({js_file, html_files[0]})

    for css_file in css_files:
        css_content = await _read_text(project_root / css_file)
        for asset in re.findall(r"""url\(\s*["']?([^"')]+)["']?\s*\)""", css_content):
            if asset.startswith(("http://", "https://", "data:", "#")):
                continue
            asset_path = (project_root / asset).resolve()
            try:
                asset_path.relative_to(project_root)
            except ValueError:
                issues.append(f"{css_file} references asset outside project root: {asset}")
                issue_targets.add(css_file)
                continue
            if not await aiofiles.ospath.exists(asset_path):
                issues.append(f"{css_file} references missing asset {asset}")
                issue_targets.add(css_file)

    if not issues:
        return [
            {
                "target_file": "__project__",
                "check": "dom_consistency",
                "exit_code": 0,
                "stdout": "DOM references ok",
                "stderr": "",
            }
        ]
    return [
        {
            "target_file": ",".join(sorted(issue_targets)) or "__project__",
            "check": "dom_consistency",
            "exit_code": 1,
            "stdout": "",
            "stderr": "; ".join(issues),
            "affected_files": sorted(issue_targets),
        }
    ]


async def _project_tests(project_root: Path) -> list[dict]:
    results: list[dict] = []
    if await aiofiles.ospath.exists(project_root / "package.json") and shutil.which("npm"):
        results.append(await _run_command(project_root, ["npm", "test", "--", "--runInBand"], timeout=30.0))
    if (await aiofiles.ospath.exists(project_root / "pytest.ini") or await aiofiles.ospath.exists(project_root / "pyproject.toml")) and shutil.which("pytest"):
        results.append(await _run_command(project_root, ["pytest", "-q"], timeout=30.0))
    return results


async def executor_node(state: dict) -> dict:
    settings = get_settings()
    project_root = (settings.projects_root / state["project_name"]).resolve()
    outputs = sorted({item for values in state.get("worker_outputs", {}).values() for item in values})
    execution_results: list[dict] = []
    runtime_errors: list[dict] = []

    for relative_path in outputs:
        path = (project_root / relative_path).resolve()
        try:
            path.relative_to(project_root)
        except ValueError:
            runtime_errors.append(
                {
                    "code": "executor_path_outside_root",
                    "severity": "error",
                    "target_file": relative_path,
                    "message": "executor refused path outside project root",
                }
            )
            continue
        if not await aiofiles.ospath.exists(path):
            runtime_errors.append(
                {
                    "code": "executor_missing_file",
                    "severity": "error",
                    "target_file": relative_path,
                    "message": "executor could not find generated file",
                }
            )
            continue
        if path.suffix == ".py":
            command_result = await _run_command(project_root, [sys.executable, "-m", "py_compile", relative_path])
            command_result.update({"target_file": relative_path, "check": "python_compile"})
            execution_results.append(command_result)
        elif path.suffix == ".json":
            command_result = await _run_command(project_root, [sys.executable, "-m", "json.tool", relative_path])
            command_result.update({"target_file": relative_path, "check": "json_parse"})
            execution_results.append(command_result)

    execution_results.extend(await _check_static_site(project_root, outputs))
    execution_results.extend(await _project_tests(project_root))

    for result in execution_results:
        if int(result.get("exit_code", 0) or 0) != 0:
            affected_files = result.get("affected_files")
            targets = affected_files if isinstance(affected_files, list) and affected_files else [result.get("target_file", "__project__")]
            for target_file in targets:
                runtime_errors.append(
                    {
                        "code": f"executor_{result.get('check', 'command')}",
                        "severity": "error",
                        "target_file": target_file,
                        "message": _clip(result.get("stderr") or result.get("stdout") or "executor command failed", limit=1_500),
                        "command": result.get("command"),
                        "exit_code": result.get("exit_code"),
                    }
                )

    status = "failed" if runtime_errors else ("passed" if execution_results or outputs else "skipped")
    updates = {
        "execution_results": execution_results,
        "runtime_errors": runtime_errors,
        "last_execution_status": status,
        "messages": [f"executor {status}"],
    }
    async with StateTransaction(state["project_id"]) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted
    return updates
