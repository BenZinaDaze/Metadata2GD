"""
webui/u115_auto_organize_store.py —— 115 云下载自动整理状态存储

记录已观察到的云下载任务完成状态，避免重复触发整理流程。
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AutoOrganizeTaskState:
    task_key: str
    info_hash: str
    task_name: str
    status: int
    percent_done: float
    wp_path_id: Optional[str]
    file_id: Optional[str]
    first_seen_at: str
    last_seen_at: str
    finished_seen_at: Optional[str]
    triggered_at: Optional[str]


_DDL = """
CREATE TABLE IF NOT EXISTS u115_auto_organize_task_state (
    task_key          TEXT PRIMARY KEY,
    info_hash         TEXT NOT NULL DEFAULT '',
    task_name         TEXT NOT NULL DEFAULT '',
    status            INTEGER NOT NULL DEFAULT 0,
    percent_done      REAL NOT NULL DEFAULT 0,
    wp_path_id        TEXT,
    file_id           TEXT,
    first_seen_at     TEXT NOT NULL,
    last_seen_at      TEXT NOT NULL,
    finished_seen_at  TEXT,
    triggered_at      TEXT
);
"""


class U115AutoOrganizeStore:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_DDL)
        self._conn.commit()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def get(self, task_key: str) -> Optional[AutoOrganizeTaskState]:
        row = self._conn.execute(
            """
            SELECT task_key, info_hash, task_name, status, percent_done, wp_path_id, file_id,
                   first_seen_at, last_seen_at, finished_seen_at, triggered_at
            FROM u115_auto_organize_task_state
            WHERE task_key = ?
            """,
            (task_key,),
        ).fetchone()
        if row is None:
            return None
        return AutoOrganizeTaskState(*row)

    def upsert_observation(
        self,
        *,
        task_key: str,
        info_hash: str,
        task_name: str,
        status: int,
        percent_done: float,
        wp_path_id: Optional[str],
        file_id: Optional[str],
        is_finished: bool,
    ) -> AutoOrganizeTaskState:
        current = self.get(task_key)
        now = self._utc_now()
        if current is None:
            finished_seen_at = now if is_finished else None
            self._conn.execute(
                """
                INSERT INTO u115_auto_organize_task_state(
                    task_key, info_hash, task_name, status, percent_done, wp_path_id, file_id,
                    first_seen_at, last_seen_at, finished_seen_at, triggered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    task_key, info_hash, task_name, status, percent_done, wp_path_id, file_id,
                    now, now, finished_seen_at,
                ),
            )
            self._conn.commit()
            return self.get(task_key)  # type: ignore[return-value]

        finished_seen_at = current.finished_seen_at
        if is_finished and not finished_seen_at:
            finished_seen_at = now
        if not is_finished:
            finished_seen_at = None

        self._conn.execute(
            """
            UPDATE u115_auto_organize_task_state
            SET info_hash = ?, task_name = ?, status = ?, percent_done = ?, wp_path_id = ?, file_id = ?,
                last_seen_at = ?, finished_seen_at = ?
            WHERE task_key = ?
            """,
            (
                info_hash, task_name, status, percent_done, wp_path_id, file_id,
                now, finished_seen_at, task_key,
            ),
        )
        self._conn.commit()
        return self.get(task_key)  # type: ignore[return-value]

    def mark_triggered(self, task_key: str) -> None:
        self._conn.execute(
            "UPDATE u115_auto_organize_task_state SET triggered_at = ? WHERE task_key = ?",
            (self._utc_now(), task_key),
        )
        self._conn.commit()

    def get_last_triggered(self) -> Optional[AutoOrganizeTaskState]:
        row = self._conn.execute(
            """
            SELECT task_key, info_hash, task_name, status, percent_done, wp_path_id, file_id,
                   first_seen_at, last_seen_at, finished_seen_at, triggered_at
            FROM u115_auto_organize_task_state
            WHERE triggered_at IS NOT NULL
            ORDER BY triggered_at DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return AutoOrganizeTaskState(*row)

    def close(self) -> None:
        self._conn.close()
