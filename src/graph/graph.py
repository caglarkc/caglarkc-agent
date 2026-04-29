from __future__ import annotations

from uuid import uuid4

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph

from src.config.settings import get_settings
from src.graph.nodes.planner import planner_node
from src.graph.nodes.reviewer import reviewer_node
from src.graph.nodes.worker import worker_node
from src.graph.state import OrchestratorState


def build_graph(checkpointer: AsyncSqliteSaver):
    builder = StateGraph(OrchestratorState)
    builder.add_node("planner", planner_node)
    builder.add_node("worker", worker_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "worker")
    builder.add_edge("worker", "reviewer")
    builder.add_edge("reviewer", END)
    return builder.compile(checkpointer=checkpointer)


async def run_minimal_graph() -> dict:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    async with AsyncSqliteSaver.from_conn_string(str(settings.graph_checkpoint_path)) as checkpointer:
        graph = build_graph(checkpointer)
        thread_id = f"{settings.graph_thread_prefix}-{uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: OrchestratorState = {
            "project_id": str(uuid4()),
            "project_name": "phase1-smoke-project",
            "task_description": "Validate the Phase 1 graph pipeline.",
            "file_registry": {},
            "dependencies": {},
            "worker_queue": [],
            "worker_status": {},
            "worker_outputs": {},
            "worker_failure_log": {},
            "current_sprint": 1,
            "sprint_type": "feature",
            "sprint_status": "planning",
            "review_cycles": 0,
            "awaiting_approval": False,
            "approval_type": "",
            "scope_changed": False,
            "context_summary": "",
            "errors": [],
            "messages": [],
        }
        result = await graph.ainvoke(initial_state, config=config)
        snapshot = await graph.aget_state(config)
        return {
            "thread_id": thread_id,
            "result": result,
            "checkpoint_values": snapshot.values,
            "checkpoint_next": list(snapshot.next),
        }
