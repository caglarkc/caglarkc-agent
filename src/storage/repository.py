from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import aiosqlite
import aiofiles.os

from src.config.settings import get_settings
from src.storage.models import Decision, FileRecord, Project, ProjectSummary, Sprint, WorkerFailureLog, utc_now


class Repository:
    def __init__(self, db_path: str | None = None) -> None:
        settings = get_settings()
        self._db_path = str(db_path or settings.sqlite_db_path)

    async def initialize(self) -> None:
        settings = get_settings()
        await aiofiles.os.makedirs(settings.data_dir, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as connection:
            await connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sprints (
                    sprint_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    number INTEGER NOT NULL,
                    sprint_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    plan_version INTEGER NOT NULL,
                    review_cycles INTEGER NOT NULL,
                    files_written_json TEXT NOT NULL,
                    decisions_json TEXT NOT NULL,
                    revision_notes_json TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS file_records (
                    file_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    sprint_id TEXT,
                    path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    worker_id TEXT,
                    checksum TEXT,
                    attempt_count INTEGER NOT NULL,
                    last_error TEXT,
                    reservation_owner TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    sprint_id TEXT,
                    summary TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS worker_failure_logs (
                    failure_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    sprint_id TEXT,
                    worker_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    retryable INTEGER NOT NULL,
                    retry_count INTEGER NOT NULL,
                    recommendation TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            try:
                await connection.execute("ALTER TABLE sprints ADD COLUMN plan_version INTEGER NOT NULL DEFAULT 1")
            except aiosqlite.OperationalError:
                pass
            await connection.commit()
        async with aiosqlite.connect(self._db_path) as connection:
            try:
                await connection.execute("ALTER TABLE file_records ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0")
            except aiosqlite.OperationalError:
                pass
            try:
                await connection.execute("ALTER TABLE file_records ADD COLUMN last_error TEXT")
            except aiosqlite.OperationalError:
                pass
            try:
                await connection.execute("ALTER TABLE file_records ADD COLUMN reservation_owner TEXT")
            except aiosqlite.OperationalError:
                pass
            try:
                await connection.execute("ALTER TABLE worker_failure_logs ADD COLUMN retryable INTEGER NOT NULL DEFAULT 1")
            except aiosqlite.OperationalError:
                pass
            try:
                await connection.execute("ALTER TABLE worker_failure_logs ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 1")
            except aiosqlite.OperationalError:
                pass
            try:
                await connection.execute("ALTER TABLE worker_failure_logs ADD COLUMN recommendation TEXT NOT NULL DEFAULT ''")
            except aiosqlite.OperationalError:
                pass
            await connection.commit()

    async def upsert_project(self, project: Project) -> None:
        async with aiosqlite.connect(self._db_path) as connection:
            await connection.execute(
                """
                INSERT INTO projects (
                    project_id, name, description, status, created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    metadata_json = excluded.metadata_json
                """,
                (
                    project.project_id,
                    project.name,
                    project.description,
                    project.status,
                    project.created_at,
                    project.updated_at,
                    json.dumps(project.metadata),
                ),
            )
            await connection.commit()

    async def get_project(self, project_id: str) -> Project | None:
        async with aiosqlite.connect(self._db_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT * FROM projects WHERE project_id = ?",
                (project_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return Project(
            project_id=row["project_id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata_json"]),
        )

    async def get_project_by_name(self, name: str) -> Project | None:
        rows = await self._fetch_all(
            "SELECT * FROM projects WHERE lower(name) = lower(?) ORDER BY created_at ASC LIMIT 1",
            (name,),
        )
        if not rows:
            return None
        row = rows[0]
        return Project(
            project_id=row["project_id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata_json"]),
        )

    async def list_projects(self) -> list[Project]:
        async with aiosqlite.connect(self._db_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute("SELECT * FROM projects ORDER BY created_at ASC")
            rows = await cursor.fetchall()
        return [
            Project(
                project_id=row["project_id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=json.loads(row["metadata_json"]),
            )
            for row in rows
        ]

    async def list_projects_by_status(self, statuses: list[str]) -> list[Project]:
        if not statuses:
            return []
        placeholders = ", ".join("?" for _ in statuses)
        rows = await self._fetch_all(
            f"SELECT * FROM projects WHERE status IN ({placeholders}) ORDER BY created_at ASC",
            statuses,
        )
        return [
            Project(
                project_id=row["project_id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=json.loads(row["metadata_json"]),
            )
            for row in rows
        ]

    async def set_project_status(self, project_id: str, status: str, *, metadata_updates: dict[str, Any] | None = None) -> None:
        project = await self.get_project(project_id)
        if project is None:
            return
        metadata = dict(project.metadata)
        if metadata_updates:
            metadata.update(metadata_updates)
        await self.upsert_project(project.model_copy(update={"status": status, "updated_at": utc_now(), "metadata": metadata}))

    async def update_project(self, project: Project) -> None:
        await self.upsert_project(project)

    async def delete_project(self, project_id: str) -> None:
        async with aiosqlite.connect(self._db_path) as connection:
            await connection.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
            await connection.commit()

    async def create_sprint(self, sprint: Sprint) -> None:
        await self._insert_model(
            table="sprints",
            payload={
                "sprint_id": sprint.sprint_id,
                "project_id": sprint.project_id,
                "number": sprint.number,
                "sprint_type": sprint.sprint_type,
                "status": sprint.status,
                "plan_version": sprint.plan_version,
                "review_cycles": sprint.review_cycles,
                "files_written_json": json.dumps(sprint.files_written),
                "decisions_json": json.dumps(sprint.decisions),
                "revision_notes_json": json.dumps(sprint.revision_notes),
                "started_at": sprint.started_at,
                "completed_at": sprint.completed_at,
            },
        )

    async def list_sprints(self, project_id: str) -> list[Sprint]:
        rows = await self._fetch_all(
            "SELECT * FROM sprints WHERE project_id = ? ORDER BY number ASC",
            (project_id,),
        )
        return [
            Sprint(
                sprint_id=row["sprint_id"],
                project_id=row["project_id"],
                number=row["number"],
                sprint_type=row["sprint_type"],
                status=row["status"],
                plan_version=row["plan_version"],
                review_cycles=row["review_cycles"],
                files_written=json.loads(row["files_written_json"]),
                decisions=json.loads(row["decisions_json"]),
                revision_notes=json.loads(row["revision_notes_json"]),
                started_at=row["started_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ]

    async def create_file_record(self, file_record: FileRecord) -> None:
        await self._insert_model(
            table="file_records",
            payload=file_record.model_dump(),
        )

    async def upsert_file_record(self, file_record: FileRecord) -> None:
        await self.create_file_record(file_record)

    async def list_file_records(self, project_id: str) -> list[FileRecord]:
        rows = await self._fetch_all(
            "SELECT * FROM file_records WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,),
        )
        return [FileRecord(**dict(row)) for row in rows]

    async def get_file_record(self, project_id: str, path: str) -> FileRecord | None:
        rows = await self._fetch_all(
            "SELECT * FROM file_records WHERE project_id = ? AND path = ? ORDER BY updated_at DESC LIMIT 1",
            (project_id, path),
        )
        if not rows:
            return None
        return FileRecord(**dict(rows[0]))

    async def create_decision(self, decision: Decision) -> None:
        await self._insert_model(table="decisions", payload=decision.model_dump())

    async def list_recent_decisions(self, project_id: str, limit: int) -> list[Decision]:
        rows = await self._fetch_all(
            """
            SELECT * FROM decisions
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (project_id, limit),
        )
        return [Decision(**dict(row)) for row in rows]

    async def create_worker_failure(self, failure: WorkerFailureLog) -> None:
        await self._insert_model(table="worker_failure_logs", payload=failure.model_dump())

    async def list_worker_failures(self, project_id: str, limit: int = 10) -> list[WorkerFailureLog]:
        rows = await self._fetch_all(
            """
            SELECT * FROM worker_failure_logs
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (project_id, limit),
        )
        return [WorkerFailureLog(**dict(row)) for row in rows]

    async def list_all_worker_failures(self, project_id: str) -> list[WorkerFailureLog]:
        rows = await self._fetch_all(
            """
            SELECT * FROM worker_failure_logs
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        )
        return [WorkerFailureLog(**dict(row)) for row in rows]

    async def project_summary(self, project_id: str) -> ProjectSummary | None:
        project = await self.get_project(project_id)
        if project is None:
            return None
        sprints = await self.list_sprints(project_id)
        file_records = await self.list_file_records(project_id)
        failures = await self.list_all_worker_failures(project_id)
        total_files_written = len({record.path for record in file_records if record.status == "done"})
        timestamps = [sprint.started_at for sprint in sprints if sprint.started_at]
        timestamps.extend(sprint.completed_at for sprint in sprints if sprint.completed_at)
        total_duration_seconds = 0
        if timestamps:
            started = min(item for item in timestamps if item)
            ended = max(item for item in timestamps if item)
            total_duration_seconds = int(
                (
                    __import__("datetime").datetime.fromisoformat(ended)
                    - __import__("datetime").datetime.fromisoformat(started)
                ).total_seconds()
            )
        worker_totals: dict[str, int] = {}
        worker_successes: dict[str, int] = {}
        retry_attempts = 0
        for record in file_records:
            if record.worker_id:
                worker_totals[record.worker_id] = worker_totals.get(record.worker_id, 0) + 1
                if record.status == "done":
                    worker_successes[record.worker_id] = worker_successes.get(record.worker_id, 0) + 1
            retry_attempts += max(record.attempt_count - 1, 0)
        worker_success_rates = {
            worker_id: round(worker_successes.get(worker_id, 0) / total, 2)
            for worker_id, total in sorted(worker_totals.items())
            if total
        }
        retry_failure_rate = round((len(failures) + retry_attempts) / max(len(file_records), 1), 2)
        return ProjectSummary(
            project_id=project.project_id,
            project_name=project.name,
            status=project.status,
            total_sprints=len(sprints),
            total_files_written=total_files_written,
            total_duration_seconds=total_duration_seconds,
            worker_success_rates=worker_success_rates,
            retry_failure_rate=retry_failure_rate,
            archived=project.status == "archived" or bool(project.metadata.get("archived", False)),
        )

    async def update_sprint_status(
        self,
        project_id: str,
        sprint_number: int,
        *,
        status: str,
        review_cycles: int | None = None,
        revision_note: str | None = None,
    ) -> None:
        sprints = await self.list_sprints(project_id)
        target = next((item for item in sprints if item.number == sprint_number), None)
        if target is None:
            return
        notes = list(target.revision_notes)
        if revision_note:
            notes.append(revision_note)
        updated = target.model_copy(
            update={
                "status": status,
                "review_cycles": review_cycles if review_cycles is not None else target.review_cycles,
                "revision_notes": notes,
            }
        )
        await self.create_sprint(updated)

    async def _insert_model(self, table: str, payload: dict[str, Any]) -> None:
        columns = list(payload.keys())
        placeholders = ", ".join(["?"] * len(columns))
        column_clause = ", ".join(columns)
        values = [payload[column] for column in columns]
        async with aiosqlite.connect(self._db_path) as connection:
            await connection.execute(
                f"INSERT OR REPLACE INTO {table} ({column_clause}) VALUES ({placeholders})",
                values,
            )
            await connection.commit()

    async def _fetch_all(self, query: str, params: Iterable[Any]) -> list[aiosqlite.Row]:
        async with aiosqlite.connect(self._db_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(query, tuple(params))
            rows = await cursor.fetchall()
        return rows
