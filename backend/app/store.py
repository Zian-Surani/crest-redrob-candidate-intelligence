from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Store:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    company TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT NOT NULL,
                    salary_min_lpa REAL NOT NULL,
                    salary_max_lpa REAL NOT NULL,
                    parsed_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    scope TEXT NOT NULL,
                    status TEXT NOT NULL,
                    processed_count INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    results_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id)
                );
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT NOT NULL,
                    user_id INTEGER,
                    properties_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_analytics_events_name
                    ON analytics_events(event_name);
                CREATE INDEX IF NOT EXISTS idx_analytics_events_created
                    ON analytics_events(created_at);
                """
            )

    def create_user(self, values: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO users
                (first_name,last_name,email,company,password_hash,created_at)
                VALUES (?,?,?,?,?,?)""",
                (
                    values["first_name"], values["last_name"], values["email"].lower(),
                    values["company"], values["password_hash"], utc_now(),
                ),
            )
            connection.commit()
            return self.get_user(cursor.lastrowid)

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT id,first_name,last_name,email,company,password_hash,created_at
                FROM users WHERE id=?""",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT id,first_name,last_name,email,company,password_hash,created_at
                FROM users WHERE email=?""",
                (email.lower(),),
            ).fetchone()
        return dict(row) if row else None

    def create_job(self, values: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO jobs
                (title,company,location,description,salary_min_lpa,salary_max_lpa,parsed_json,status,created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    values["title"], values["company"], values["location"],
                    values["description"], values["salary_min_lpa"], values["salary_max_lpa"],
                    json.dumps(values["parsed"]), values.get("status", "Active"), utc_now(),
                ),
            )
            connection.commit()
            return self.get_job(cursor.lastrowid)

    def get_job(self, job_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT id,title,company,location,description,salary_min_lpa,
                salary_max_lpa,parsed_json,status,created_at FROM jobs WHERE id=?""",
                (job_id,),
            ).fetchone()
        return self._job(dict(row)) if row else None

    def list_jobs(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT id,title,company,location,description,salary_min_lpa,
                salary_max_lpa,parsed_json,status,created_at FROM jobs ORDER BY id DESC"""
            ).fetchall()
        return [self._job(dict(row)) for row in rows]

    @staticmethod
    def _job(row: dict[str, Any]) -> dict[str, Any]:
        row["parsed"] = json.loads(row.pop("parsed_json"))
        return row

    def save_ranking(self, values: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO rankings
                (job_id,scope,status,processed_count,duration_seconds,results_json,metrics_json,created_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                (
                    values["job_id"], values["scope"], "Completed", values["processed_count"],
                    values["duration_seconds"], json.dumps(values["results"]),
                    json.dumps(values["metrics"]), utc_now(),
                ),
            )
            connection.commit()
            return self.get_ranking(cursor.lastrowid)

    def get_ranking(self, ranking_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT id,job_id,scope,status,processed_count,duration_seconds,
                results_json,metrics_json,created_at FROM rankings WHERE id=?""",
                (ranking_id,),
            ).fetchone()
        return self._ranking(dict(row)) if row else None

    def latest_ranking(self, job_id: int | None = None) -> dict[str, Any] | None:
        query = (
            "SELECT id,job_id,scope,status,processed_count,duration_seconds,"
            "results_json,metrics_json,created_at FROM rankings"
        )
        params: tuple[Any, ...] = ()
        if job_id is not None:
            query += " WHERE job_id=?"
            params = (job_id,)
        query += " ORDER BY id DESC LIMIT 1"
        with self.connect() as connection:
            row = connection.execute(query, params).fetchone()
        return self._ranking(dict(row)) if row else None

    def list_rankings(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT id,job_id,scope,status,processed_count,duration_seconds,
                results_json,metrics_json,created_at FROM rankings ORDER BY id DESC LIMIT 20"""
            ).fetchall()
        return [self._ranking(dict(row)) for row in rows]

    def track_event(
        self, event_name: str, properties: dict[str, Any] | None = None,
        user_id: int | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO analytics_events
                (event_name,user_id,properties_json,created_at) VALUES (?,?,?,?)""",
                (event_name, user_id, json.dumps(properties or {}), utc_now()),
            )

    def event_summary(self) -> dict[str, Any]:
        with self.connect() as connection:
            totals = connection.execute(
                """SELECT event_name, COUNT(*) AS count
                FROM analytics_events GROUP BY event_name ORDER BY count DESC"""
            ).fetchall()
            recent = connection.execute(
                """SELECT event_name, properties_json, created_at
                FROM analytics_events ORDER BY id DESC LIMIT 12"""
            ).fetchall()
        return {
            "counts": [dict(row) for row in totals],
            "recent": [
                {
                    "event_name": row["event_name"],
                    "properties": json.loads(row["properties_json"]),
                    "created_at": row["created_at"],
                }
                for row in recent
            ],
        }

    @staticmethod
    def _ranking(row: dict[str, Any]) -> dict[str, Any]:
        row["results"] = json.loads(row.pop("results_json"))
        row["metrics"] = json.loads(row.pop("metrics_json"))
        return row
