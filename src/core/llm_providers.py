from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.settings import Settings, get_settings
from src.core.contracts import DispatchAssignment


CONTEXT_MAX_CHARS = 4_000
RELATED_FILE_MAX_CHARS = 1_800


@dataclass(frozen=True)
class WorkerModelConfig:
    provider: str
    model_name: str
    auth_available: bool = True
    missing_auth_message: str = ""


@dataclass(frozen=True)
class GeneratedFileContent:
    content: str
    provider: str
    model_name: str
    used_stub: bool = False
    fallback_reason: str | None = None


class InvalidGeneratedArtifactError(ValueError):
    pass


def _render_stub_file_content(target_file: str, *, task_description: str = "") -> str:
    task_note = task_description.strip() or "generated project"
    lowered_task = task_note.lower()
    if ("borç" in lowered_task or "borc" in lowered_task or "debt" in lowered_task) and target_file.endswith(".html"):
        css_name = "styles.css"
        js_name = "script.js"
        return (
            "<!doctype html>\n"
            '<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>Borc Takip</title>\n"
            f'<link rel="stylesheet" href="{css_name}">\n'
            "</head>\n<body>\n"
            '<main class="app-shell">\n'
            "<h1>Borc Takip</h1>\n"
            '<section class="summary"><span>Toplam</span><strong id="total-debt">0 TL</strong></section>\n'
            '<form id="debt-form">\n'
            '<input id="debtor-name" name="name" placeholder="Borclu adi" required>\n'
            '<input id="debt-amount" name="amount" type="number" min="0.01" step="0.01" placeholder="Tutar" required>\n'
            '<button type="submit">Ekle</button>\n'
            "</form>\n"
            '<table><thead><tr><th>Kisi</th><th>Tutar</th><th></th></tr></thead><tbody id="debt-list-body"></tbody></table>\n'
            "</main>\n"
            f'<script src="{js_name}"></script>\n'
            "</body>\n</html>\n"
        )
    if ("borç" in lowered_task or "borc" in lowered_task or "debt" in lowered_task) and target_file.endswith(".css"):
        return (
            "body { margin: 0; font-family: Arial, sans-serif; background: #f4f7f8; color: #1f2933; }\n"
            ".app-shell { max-width: 860px; margin: 32px auto; padding: 24px; background: white; border-radius: 8px; }\n"
            ".summary { display: flex; justify-content: space-between; padding: 16px; background: #e8f3ef; border-radius: 6px; margin-bottom: 16px; }\n"
            "form { display: grid; grid-template-columns: 1fr 160px auto; gap: 10px; margin-bottom: 18px; }\n"
            "input, button { padding: 10px 12px; border: 1px solid #cbd5df; border-radius: 6px; }\n"
            "button { background: #256c5c; color: white; cursor: pointer; }\n"
            "table { width: 100%; border-collapse: collapse; }\n"
            "th, td { padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: left; }\n"
            ".delete-btn { background: #b42318; }\n"
            "@media (max-width: 680px) { form { grid-template-columns: 1fr; } .app-shell { margin: 0; min-height: 100vh; border-radius: 0; } }\n"
        )
    if ("borç" in lowered_task or "borc" in lowered_task or "debt" in lowered_task) and target_file.endswith(".js"):
        return (
            "document.addEventListener('DOMContentLoaded', () => {\n"
            "  const form = document.getElementById('debt-form');\n"
            "  const nameInput = document.getElementById('debtor-name');\n"
            "  const amountInput = document.getElementById('debt-amount');\n"
            "  const listBody = document.getElementById('debt-list-body');\n"
            "  const totalDebt = document.getElementById('total-debt');\n"
            "  let debts = JSON.parse(localStorage.getItem('debts') || '[]');\n"
            "  const save = () => localStorage.setItem('debts', JSON.stringify(debts));\n"
            "  const render = () => {\n"
            "    listBody.innerHTML = '';\n"
            "    let total = 0;\n"
            "    debts.forEach((debt, index) => {\n"
            "      total += Number(debt.amount) || 0;\n"
            "      const row = document.createElement('tr');\n"
            "      row.innerHTML = `<td>${debt.name}</td><td>${Number(debt.amount).toFixed(2)} TL</td><td><button class=\"delete-btn\" data-index=\"${index}\">Sil</button></td>`;\n"
            "      listBody.appendChild(row);\n"
            "    });\n"
            "    totalDebt.textContent = `${total.toFixed(2)} TL`;\n"
            "  };\n"
            "  form.addEventListener('submit', (event) => {\n"
            "    event.preventDefault();\n"
            "    const name = nameInput.value.trim();\n"
            "    const amount = Number(amountInput.value);\n"
            "    if (!name || amount <= 0) return;\n"
            "    debts.push({ name, amount });\n"
            "    save();\n"
            "    form.reset();\n"
            "    render();\n"
            "  });\n"
            "  listBody.addEventListener('click', (event) => {\n"
            "    const button = event.target.closest('.delete-btn');\n"
            "    if (!button) return;\n"
            "    debts.splice(Number(button.dataset.index), 1);\n"
            "    save();\n"
            "    render();\n"
            "  });\n"
            "  render();\n"
            "});\n"
        )
    if target_file == "api_contract.json":
        return json.dumps({"version": "1.0.0", "description": task_note[:120], "endpoints": []}, indent=2) + "\n"
    if target_file == "shared_types.py":
        return (
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class SharedPayload:\n"
            "    name: str\n"
        )
    if target_file == "src/__init__.py":
        return '"""Generated project package."""\n'
    if target_file == "helpers.py":
        return (
            "def helper() -> str:\n"
            f"    return {task_note[:80]!r}\n"
        )
    if target_file == "app.py":
        return (
            "from helpers import helper\n\n"
            "def run() -> str:\n"
            "    return helper()\n"
        )
    if target_file.endswith(".json"):
        return "{}\n"
    if target_file == "index.html":
        return (
            "<!doctype html>\n"
            '<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>Restoran</title>\n"
            '<link rel="stylesheet" href="styles.css">\n'
            "</head>\n<body>\n"
            '<header><nav><button id="menu-button">Menu</button><ul id="nav-menu"><li><a href="#rezervasyon">Rezervasyon</a></li></ul></nav></header>\n'
            '<main><section id="hero"><h1>Restoran</h1></section><section id="rezervasyon"><form><input name="name"><button type="submit">Gonder</button></form></section></main>\n'
            '<script src="script.js"></script>\n</body>\n</html>\n'
        )
    if target_file in {"styles.css", "style.css"}:
        return "body { font-family: Arial, sans-serif; margin: 0; } #nav-menu.open { display: block; }\n"
    if target_file == "script.js":
        return (
            "document.addEventListener('DOMContentLoaded', () => {\n"
            "  const button = document.getElementById('menu-button');\n"
            "  const menu = document.getElementById('nav-menu');\n"
            "  if (button && menu) button.addEventListener('click', () => menu.classList.toggle('open'));\n"
            "  const form = document.querySelector('#rezervasyon form');\n"
            "  if (form) form.addEventListener('submit', (event) => event.preventDefault());\n"
            "});\n"
        )
    return f"# generated fallback for {target_file}\n"


def _compact_text(value: Any, *, max_chars: int = CONTEXT_MAX_CHARS) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}... [truncated]"


def _safe_read_project_file(project_name: str, relative_path: str, *, max_chars: int = RELATED_FILE_MAX_CHARS) -> str | None:
    if ".." in Path(relative_path).parts:
        return None
    project_root = get_settings().projects_root / project_name
    path = (project_root / relative_path).resolve()
    try:
        path.relative_to(project_root.resolve())
    except ValueError:
        return None
    if not path.exists() or not path.is_file():
        return None
    try:
        return _compact_text(path.read_text(encoding="utf-8", errors="replace"), max_chars=max_chars)
    except OSError:
        return None


def _related_file_snapshots(state: dict, target_file: str) -> str:
    files = sorted(state.get("file_registry", {}).keys())
    if target_file not in files:
        files.append(target_file)
    relevant: list[str] = []
    target_suffix = Path(target_file).suffix.lower()
    frontend_suffixes = {".html", ".css", ".js"}
    if target_suffix in frontend_suffixes:
        relevant = [path for path in files if Path(path).suffix.lower() in frontend_suffixes]
    else:
        relevant = [target_file]
        for issue in [*state.get("validation_issues", []), *state.get("runtime_errors", []), *state.get("revision_tasks", [])]:
            issue_target = issue.get("target_file")
            if isinstance(issue_target, str) and issue_target not in relevant and issue_target != "__project__":
                relevant.append(issue_target)
    chunks: list[str] = []
    for relative_path in relevant[:6]:
        content = _safe_read_project_file(str(state.get("project_name", "")), relative_path)
        if content is None:
            continue
        marker = "TARGET" if relative_path == target_file else "RELATED"
        chunks.append(f"--- {marker} FILE: {relative_path} ---\n{content}")
    return "\n\n".join(chunks) if chunks else "None"


def _worker_model_config(worker_id: str, settings: Settings) -> WorkerModelConfig:
    if settings.gemini_api_key:
        return WorkerModelConfig(provider="gemini", model_name=settings.gemini_model)
    return WorkerModelConfig(
        provider="gemini",
        model_name=settings.gemini_model,
        auth_available=False,
        missing_auth_message="GEMINI_API_KEY is missing",
    )


def _chat_model_for(config: WorkerModelConfig, settings: Settings):
    return ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=settings.gemini_api_key,
        timeout=settings.http_timeout_seconds,
        temperature=0,
    )


def build_worker_prompt(state: dict, assignment: DispatchAssignment) -> tuple[str, str]:
    target_file = assignment.target_file
    suffix = Path(target_file).suffix
    output_rules = [
        "Return only the raw file body for this path (single artifact, no preamble).",
        "Return exactly one file body for the requested path.",
        "Do not include Markdown fences, explanations, greetings, or filenames.",
        "Do not include prompt-injection phrases such as 'ignore previous instructions' or 'prompt override'.",
        "Do not reference absolute filesystem paths, home directories, /etc, or path traversal.",
    ]
    if suffix == ".json":
        output_rules.append("The output must be valid JSON.")
    if suffix == ".py":
        output_rules.append("The output must be valid Python syntax with only standard-library or local imports.")
    if suffix in {".html", ".css", ".js"}:
        output_rules.extend(
            [
                "When repairing frontend files, align HTML, CSS, and JavaScript selectors exactly with the related snapshots.",
                "If this is HTML, link the exact generated CSS and JavaScript filenames listed in the project plan.",
                "If feedback says a selector/id/class is missing and this target is HTML, add the missing matching element.",
                "If feedback says a selector/id/class is missing and this target is JavaScript, either use an existing selector from HTML or guard querySelector/getElementById results before addEventListener/classList access.",
                "If feedback says a local CSS asset is missing, remove the url(...) dependency or replace it with a CSS-only gradient/color.",
            ]
        )
    if suffix == ".html":
        output_rules.append("Return one complete HTML document only; do not append JSON, plans, notes, or text after </html>.")
    related_issues = [
        issue
        for issue in [*state.get("revision_tasks", []), *state.get("validation_issues", []), *state.get("runtime_errors", [])]
        if issue.get("target_file") in {target_file, "__project__"}
    ]
    issue_lines = []
    for issue in related_issues[-8:]:
        issue_lines.append(
            f"- {issue.get('code', 'issue')}: {issue.get('reason') or issue.get('message') or issue.get('error')}"
        )
    execution_context = state.get("execution_results", [])[-8:]
    related_snapshots = _related_file_snapshots(state, target_file)

    system_prompt = (
        "You are a careful code-generation worker inside an orchestrated software team. "
        "You produce production-ready file contents that satisfy the user's intent and local validator policy. "
        + " ".join(output_rules)
    )
    user_prompt = "\n".join(
        [
            "User task:",
            _compact_text(state.get("task_description"), max_chars=1_200),
            "",
            "Sprint type:",
            _compact_text(state.get("sprint_type"), max_chars=120),
            "",
            "Assignment:",
            _compact_text(assignment.description, max_chars=800),
            "",
            "Target file:",
            target_file,
            "",
            "Context summary:",
            _compact_text(state.get("context_summary"), max_chars=CONTEXT_MAX_CHARS),
            "",
            "Previous validation/runtime feedback for this target:",
            "\n".join(issue_lines) if issue_lines else "None",
            "",
            "Recent executor output:",
            _compact_text(json.dumps(execution_context, ensure_ascii=True), max_chars=2_000) if execution_context else "None",
            "",
            "Current related file snapshots:",
            related_snapshots,
            "",
            "Generate only the raw file body now.",
        ]
    )
    return system_prompt, user_prompt


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


def _strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return content.rstrip() + "\n"
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).rstrip() + "\n"
    return content.rstrip() + "\n"


def _normalize_generated_artifact(content: str, target_file: str) -> str:
    stripped = _strip_markdown_fence(content).strip()
    if target_file.endswith(".html"):
        stripped = _strip_embedded_planner_json_scripts(stripped)
        lowered = stripped.lower()
        closing_index = lowered.rfind("</html>")
        if closing_index >= 0:
            stripped = stripped[: closing_index + len("</html>")].rstrip()
    if Path(target_file).suffix.lower() in {".html", ".css", ".js"}:
        stripped = _strip_trailing_json_note(stripped)
    if not stripped.startswith("{"):
        return stripped.rstrip() + "\n"
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped.rstrip() + "\n"
    if isinstance(payload, dict):
        files = payload.get("files")
        if isinstance(files, list):
            for item in files:
                if not isinstance(item, dict):
                    continue
                if item.get("path") == target_file and isinstance(item.get("content"), str):
                    return item["content"].rstrip() + "\n"
        if isinstance(payload.get("content"), str):
            return payload["content"].rstrip() + "\n"
        if Path(target_file).suffix.lower() != ".json" and {"execution_intent", "project_plan", "plan", "tasks", "files"}.intersection(payload):
            raise InvalidGeneratedArtifactError("model returned planner JSON instead of raw file content")
    return stripped.rstrip() + "\n"


def _strip_embedded_planner_json_scripts(content: str) -> str:
    def replace_if_planner(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return match.group(0)
        if isinstance(payload, dict) and {"execution_intent", "project_plan", "plan", "tasks", "files"}.intersection(payload):
            return ""
        return match.group(0)

    return re.sub(
        r"""<script\b[^>]*type=["']application/json["'][^>]*>(.*?)</script>""",
        replace_if_planner,
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _strip_trailing_json_note(content: str) -> str:
    for marker in ("\n{", "\r\n{"):
        index = content.rfind(marker)
        if index < 0:
            continue
        candidate = content[index + 1 :].strip()
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and {"execution_intent", "plan", "tasks", "files"}.intersection(payload):
            return content[:index].rstrip()
    return content


def _align_html_asset_links(content: str, state: dict) -> str:
    planned_files = sorted(state.get("file_registry", {}).keys())
    css_files = [Path(path).name for path in planned_files if Path(path).suffix.lower() == ".css"]
    js_files = [Path(path).name for path in planned_files if Path(path).suffix.lower() == ".js"]
    if len(css_files) == 1:
        css_name = css_files[0]
        content = re.sub(
            r"""(<link\b[^>]*\brel=["']stylesheet["'][^>]*\bhref=["'])([^"']+)(["'][^>]*>)""",
            lambda match: f"{match.group(1)}{css_name}{match.group(3)}",
            content,
            flags=re.IGNORECASE,
        )
    if len(js_files) == 1:
        js_name = js_files[0]
        content = re.sub(
            r"""(<script\b[^>]*\bsrc=["'])([^"']+)(["'][^>]*>\s*</script>)""",
            lambda match: f"{match.group(1)}{js_name}{match.group(3)}",
            content,
            flags=re.IGNORECASE,
        )
    return content


async def _direct_chat_response(config: WorkerModelConfig, settings: Settings, system_prompt: str, user_prompt: str) -> str | None:
    if config.provider == "gemini":
        if not settings.gemini_api_key:
            return None
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            response = await client.post(
                f"{settings.gemini_base_url.rstrip('/')}/v1beta/models/{config.model_name}:generateContent",
                params={"key": settings.gemini_api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": user_prompt}],
                        }
                    ],
                    "generationConfig": {"temperature": 0},
                },
            )
            response.raise_for_status()
            payload = response.json()
        parts = (((payload.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
        return "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
    return None


def _fallback_chain(settings: Settings) -> list[WorkerModelConfig]:
    """Returns the worker provider chain. Workers are Gemini-only."""
    chain = []
    if settings.gemini_api_key:
        chain.append(WorkerModelConfig(provider="gemini", model_name=settings.gemini_model))
    return chain


async def _try_provider(config: WorkerModelConfig, settings: Settings, system_prompt: str, user_prompt: str) -> str:
    direct_content = await _direct_chat_response(config, settings, system_prompt, user_prompt)
    if direct_content is not None:
        return _strip_markdown_fence(_content_to_text(direct_content))
    model = _chat_model_for(config, settings)
    response = await asyncio.wait_for(
        model.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]),
        timeout=max(5.0, settings.http_timeout_seconds + 5.0),
    )
    return _strip_markdown_fence(_content_to_text(response.content))


async def _repair_provider_output(
    config: WorkerModelConfig,
    settings: Settings,
    *,
    target_file: str,
    invalid_content: str,
    original_user_prompt: str,
) -> str:
    suffix = Path(target_file).suffix.lower().lstrip(".") or "text"
    repair_system = (
        "You repair invalid code-generation worker outputs. "
        f"Return only the raw {suffix} file body for {target_file}. "
        "Do not return JSON, plans, Markdown fences, explanations, or filenames."
    )
    repair_user = "\n".join(
        [
            "Original assignment context:",
            _compact_text(original_user_prompt, max_chars=2_000),
            "",
            "Invalid previous output:",
            _compact_text(invalid_content, max_chars=2_000),
            "",
            f"Return only the corrected raw file body for {target_file}.",
        ]
    )
    return await _try_provider(config, settings, repair_system, repair_user)


async def generate_file_content(state: dict, assignment: DispatchAssignment) -> GeneratedFileContent:
    settings = get_settings()
    primary_config = _worker_model_config(assignment.worker_id, settings)

    if settings.worker_use_stub:
        return GeneratedFileContent(
            content=_render_stub_file_content(assignment.target_file, task_description=state.get("task_description", "")),
            provider=primary_config.provider,
            model_name=primary_config.model_name,
            used_stub=True,
            fallback_reason="WORKER_USE_STUB enabled",
        )

    system_prompt, user_prompt = build_worker_prompt(state, assignment)
    chain = _fallback_chain(settings)
    last_error: Exception | None = None

    for config in chain:
        try:
            raw_content = await _try_provider(config, settings, system_prompt, user_prompt)
            used_stub = False
            fallback_reason = None
            try:
                content = _normalize_generated_artifact(raw_content, assignment.target_file)
            except InvalidGeneratedArtifactError:
                try:
                    repaired = await _repair_provider_output(
                        config,
                        settings,
                        target_file=assignment.target_file,
                        invalid_content=raw_content,
                        original_user_prompt=user_prompt,
                    )
                    content = _normalize_generated_artifact(repaired, assignment.target_file)
                except InvalidGeneratedArtifactError:
                    content = _render_stub_file_content(
                        assignment.target_file,
                        task_description=state.get("task_description", ""),
                    )
                    used_stub = True
                    fallback_reason = "Gemini returned planner JSON twice; used safe frontend template"
            if assignment.target_file.endswith(".html"):
                content = _align_html_asset_links(content, state)
            fallback_reason = fallback_reason or (
                f"fallback from {primary_config.provider}" if config.provider != primary_config.provider else None
            )
            return GeneratedFileContent(
                content=content,
                provider=config.provider,
                model_name=config.model_name,
                used_stub=used_stub,
                fallback_reason=fallback_reason,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    raise RuntimeError("all Gemini worker providers failed")
