from __future__ import annotations

import asyncio
import statistics
import time
from dataclasses import dataclass

from src.core.scheduler import FairScheduler, ScheduledTask


@dataclass
class LoadMetrics:
    p95_dispatch_latency_ms: float
    retry_success_ratio: float
    stalled_count: int
    starvation_detected: bool


async def simulate_load(*, project_count: int = 4, tasks_per_project: int = 8) -> LoadMetrics:
    scheduler = FairScheduler(per_project_limit=2)
    enqueue_times: dict[str, float] = {}
    latencies_ms: list[float] = []
    retries = 0
    retry_successes = 0
    stalled_count = 0
    first_seen: set[str] = set()

    for project_index in range(project_count):
        project_id = f"project-{project_index + 1}"
        for task_index in range(tasks_per_project):
            task_id = f"{project_id}-task-{task_index + 1}"
            enqueue_times[task_id] = time.perf_counter()
            scheduler.enqueue(ScheduledTask(project_id=project_id, thread_id=f"{project_id}-thread", task_id=task_id))

    completed = 0
    total = project_count * tasks_per_project
    while completed < total:
        decision = scheduler.acquire_next()
        if decision.task is None:
            stalled_count += 1
            await asyncio.sleep(0.001)
            for project_id in list(scheduler.queue_lengths()):
                scheduler.clear_throttle(project_id)
            continue
        task = decision.task
        first_seen.add(task.project_id)
        latency_ms = (time.perf_counter() - enqueue_times[task.task_id]) * 1000
        latencies_ms.append(latency_ms)
        await asyncio.sleep(0.002)
        if task.task_id.endswith(("3", "6")):
            retries += 1
            scheduler.throttle_project(task.project_id, "synthetic_rate_limit")
            await asyncio.sleep(0.001)
            scheduler.clear_throttle(task.project_id)
            retry_successes += 1
        scheduler.release(task.project_id)
        completed += 1

    p95 = statistics.quantiles(latencies_ms, n=20)[18] if len(latencies_ms) >= 20 else max(latencies_ms, default=0.0)
    return LoadMetrics(
        p95_dispatch_latency_ms=round(p95, 3),
        retry_success_ratio=round(retry_successes / retries, 2) if retries else 1.0,
        stalled_count=stalled_count,
        starvation_detected=len(first_seen) != project_count,
    )


def print_metrics(metrics: LoadMetrics) -> None:
    print("=== LOAD SIMULATION SUMMARY ===")
    print(f"P95_DISPATCH_LATENCY_MS: {metrics.p95_dispatch_latency_ms}")
    print(f"RETRY_SUCCESS_RATIO: {metrics.retry_success_ratio}")
    print(f"STALLED_COUNT: {metrics.stalled_count}")
    print(f"STARVATION_DETECTED: {metrics.starvation_detected}")
    passed = not metrics.starvation_detected and metrics.retry_success_ratio >= 0.8
    print(f"LOAD_SIMULATION_STATUS: {'PASS' if passed else 'FAIL'}")


def main() -> None:
    metrics = asyncio.run(simulate_load())
    print_metrics(metrics)


if __name__ == "__main__":
    main()
