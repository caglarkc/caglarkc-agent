"""
Gercek API testi - stub yok, legacy planner + OpenRouter/Ollama fallback ile kod uretimi.
Ollama lokalda yoksa OpenRouter'a dusuyor.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("USE_LEGACY_PLANNER", "true")
# WORKER_USE_STUB intentionally NOT set

from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.graph.graph import build_thread_config, graph_runtime
from src.graph.state import build_initial_state
from src.storage.repository import Repository

CHECKPOINT_PATH = Path("data/real_api_test.sqlite")


async def run_real_test():
    print("=" * 60)
    print("GERCEK API TESTI - Stub yok")
    print("Worker: Ollama -> OpenRouter fallback")
    print("Reviewer: Gemini")
    print("=" * 60)

    bus = EventBus()
    await bus.reset()
    manager = GraphManager(event_bus=bus)
    await manager.start()

    repo = Repository()
    await repo.initialize()

    thread_id = f"real-api-{uuid4().hex[:8]}"
    config = build_thread_config(thread_id)
    manager.register_thread(thread_id, config)

    initial_state = build_initial_state(
        project_name="flask-web-app",
        task_description="Basit bir Flask web uygulamasi: anasayfa route, JSON API endpoint ve requirements.txt",
        current_thread_id=thread_id,
    )

    print(f"\n[1] Thread: {thread_id}")

    async with graph_runtime(CHECKPOINT_PATH) as graph:
        manager.attach_graph(graph)

        print("[2] Planner calistiriliyor...")
        paused = await graph.ainvoke(initial_state, config=config)

        awaiting = paused.get("awaiting_approval")
        approval_id = paused.get("active_approval_id")
        files = [q["assignment"]["target_file"] for q in paused.get("worker_queue", [])]
        print(f"    awaiting_approval: {awaiting}")
        print(f"    dosyalar: {files}")

        if not awaiting or not approval_id:
            print("[FAIL] Planner approval pause olusturamadi!")
            return

        print("\n[3] Plan onaylaniyor - gercek API cagrilari basliyor...")
        project_id = paused["project_id"]
        await bus.emit(
            "plan.approved",
            new_event(
                "plan.approved",
                payload={"approval_id": approval_id, "decision": "approved"},
                project_id=project_id,
                thread_id=thread_id,
                sprint_id=f"sprint-{paused['current_sprint']}",
                correlation_id=project_id,
                idempotency_key=f"approve-{thread_id}",
            ).model_dump(),
        )

        final_snapshot = await graph.aget_state(config)
        final = final_snapshot.values

    print("\n" + "=" * 60)
    print(f"sprint_status    : {final.get('sprint_status')}")
    print(f"review_cycles    : {final.get('review_cycles')}")
    print(f"reviewer_decision: {final.get('reviewer_decision')}")
    print("\nMesajlar:")
    for msg in final.get("messages", []):
        print(f"  {msg}")

    errors = final.get("errors", [])
    if errors:
        print(f"\nHatalar: {errors}")

    project_root = Path("projects/flask-web-app")
    if project_root.exists():
        code_files = [f for f in project_root.rglob("*") if f.is_file() and ".meta" not in str(f)]
        print(f"\nUretilen {len(code_files)} dosya:")
        for f in code_files:
            content = f.read_text(errors="replace")
            print(f"\n{'='*40}")
            print(f"  {f.relative_to(project_root)}")
            print(f"{'='*40}")
            print(content[:800])
            if len(content) > 800:
                print(f"... (+{len(content)-800} karakter daha)")
    else:
        print("\n[!] Proje klasoru olusturulmadi - worker basarisiz olmus olabilir")

    passed = final.get("sprint_status") == "approved"
    print("\n" + "=" * 60)
    print(f"{'PASS - Gercek API ile kod uretildi!' if passed else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_real_test())
