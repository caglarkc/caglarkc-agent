from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles.os
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph

from src.config.settings import get_settings
from src.graph.edges import route_after_dispatch, route_after_planner, route_after_review, route_after_worker
from src.graph.nodes.dispatcher import dispatcher_node
from src.graph.nodes.planner import planner_node
from src.graph.nodes.reviewer import reviewer_node
from src.graph.nodes.validator import validator_node
from src.graph.nodes.worker import worker_node
from src.graph.state import OrchestratorState, build_initial_state


def build_thread_config(thread_id: str) -> dict:
    if not thread_id or not thread_id.strip():
        raise ValueError("thread_id is required")
    return {"configurable": {"thread_id": thread_id.strip()}}


def build_graph(checkpointer: AsyncSqliteSaver):
    builder = StateGraph(OrchestratorState)
    builder.add_node("planner", planner_node)
    builder.add_node("dispatcher", dispatcher_node)
    builder.add_node("worker", worker_node)
    builder.add_node("validator", validator_node)
    builder.add_node("reviewer", reviewer_node)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges("planner", route_after_planner, {"dispatcher": "dispatcher", END: END})
    builder.add_conditional_edges("dispatcher", route_after_dispatch, {"worker": "worker", "reviewer": "reviewer"})
    builder.add_conditional_edges("worker", route_after_worker, {"validator": "validator"})
    builder.add_edge("validator", "reviewer")
    builder.add_conditional_edges("reviewer", route_after_review, {"dispatcher": "dispatcher", END: END})
    return builder.compile(checkpointer=checkpointer)


@asynccontextmanager
async def graph_runtime(checkpoint_path: str | Path | None = None):
    settings = get_settings()
    resolved_path = Path(checkpoint_path or settings.graph_checkpoint_path)
    await aiofiles.os.makedirs(resolved_path.parent, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(resolved_path)) as checkpointer:
        yield build_graph(checkpointer)


async def run_graph_once(
    *,
    thread_id: str,
    project_name: str,
    task_description: str,
    checkpoint_path: str | Path | None = None,
) -> dict:
    async with graph_runtime(checkpoint_path) as graph:
        config = build_thread_config(thread_id)
        initial_state = build_initial_state(
            project_name=project_name,
            task_description=task_description,
            current_thread_id=thread_id,
        )
        result = await graph.ainvoke(initial_state, config=config)
        snapshot = await graph.aget_state(config)
        return {"result": result, "snapshot": snapshot.values, "next": list(snapshot.next)}
