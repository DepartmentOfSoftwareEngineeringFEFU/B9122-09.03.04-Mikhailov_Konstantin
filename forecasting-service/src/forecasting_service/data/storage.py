import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from forecasting_service.config import (
    DATASETS_DIR,
    DETAIL_FIELDS,
    COVERAGE_FIELDS,
)


class DetailStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"



_LISTING_NUMERIC_FIELDS = (
    "price", "total_meters", "rooms_count", "floor", "floors_count",
)

_LISTING_TEXT_FIELDS = (
    "district", "microdistrict", "street", "house_number",
    "residential_complex", "underground", "address_raw", "title_raw",
)


class FlatStorage:
    def __init__(self, db_name: str = "flats.db"):
        DATASETS_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = DATASETS_DIR / db_name
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()


    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), timeout=30)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS flats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                cian_id INTEGER,

                price INTEGER,

                total_meters REAL,
                rooms_count INTEGER,
                floor INTEGER,
                floors_count INTEGER,

                district TEXT DEFAULT '',
                microdistrict TEXT DEFAULT '',
                street TEXT DEFAULT '',
                house_number TEXT DEFAULT '',
                underground TEXT DEFAULT '',
                residential_complex TEXT DEFAULT '',
                address_raw TEXT DEFAULT '',

                living_meters REAL,
                kitchen_meters REAL,
                ceiling_height REAL,
                object_type TEXT DEFAULT '',
                layout_type TEXT DEFAULT '',
                bathroom_type TEXT DEFAULT '',
                bathroom_count INTEGER,
                window_view TEXT DEFAULT '',
                finish_type TEXT DEFAULT '',
                balcony_count INTEGER,
                loggia_count INTEGER,
                has_furniture INTEGER,

                year_of_construction INTEGER,
                house_material_type TEXT DEFAULT '',
                floor_type TEXT DEFAULT '',
                elevator_passenger INTEGER,
                elevator_cargo INTEGER,
                entrances_count INTEGER,
                has_garbage_chute INTEGER,
                has_ramp INTEGER,
                has_concierge INTEGER,
                parking_type TEXT DEFAULT '',
                heating_type TEXT DEFAULT '',
                is_emergency INTEGER,

                jk_name TEXT DEFAULT '',
                jk_class TEXT DEFAULT '',
                jk_deadline TEXT DEFAULT '',
                developer TEXT DEFAULT '',

                cadastral_number TEXT DEFAULT '',
                encumbrances TEXT DEFAULT '',
                owners_count INTEGER,

                title_raw TEXT DEFAULT '',
                author TEXT DEFAULT '',
                author_type TEXT DEFAULT '',

                detail_status TEXT DEFAULT 'pending',
                detail_attempts INTEGER DEFAULT 0,
                last_attempt_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_detail_status
                ON flats(detail_status);
            CREATE INDEX IF NOT EXISTS idx_cian_id
                ON flats(cian_id);
            CREATE INDEX IF NOT EXISTS idx_district
                ON flats(district);
        """)
        conn.commit()
        logger.info(f"  БД инициализирована: {self.db_path}")


    def upsert_from_listing(
        self,
        flat_dict: dict,
        *,
        _commit: bool = True,
    ) -> bool:
        conn = self._get_conn()
        url = flat_dict.get("url", "")
        if not url:
            return False

        existing = conn.execute(
            "SELECT id FROM flats WHERE url = ?", (url,)
        ).fetchone()

        if existing:
            self._update_from_listing(conn, flat_dict, url)
            if _commit:
                conn.commit()
            return False

        self._insert_from_listing(conn, flat_dict, url)
        if _commit:
            conn.commit()
        return True

    def _update_from_listing(
        self,
        conn: sqlite3.Connection,
        flat_dict: dict,
        url: str,
    ) -> None:
        set_parts = []
        values = []

        for field in _LISTING_NUMERIC_FIELDS:
            set_parts.append(f"{field} = COALESCE(?, {field})")
            values.append(flat_dict.get(field))

        for field in _LISTING_TEXT_FIELDS:
            set_parts.append(f"{field} = CASE WHEN ? != '' THEN ? ELSE {field} END")
            val = flat_dict.get(field, "")
            values.extend([val, val])

        set_parts.append("updated_at = datetime('now')")
        values.append(url)

        sql = f"UPDATE flats SET {', '.join(set_parts)} WHERE url = ?"
        conn.execute(sql, values)

    def _insert_from_listing(
        self,
        conn: sqlite3.Connection,
        flat_dict: dict,
        url: str,
    ) -> None:
        all_fields = ("url", "cian_id") + _LISTING_NUMERIC_FIELDS + _LISTING_TEXT_FIELDS
        field_names = ", ".join(all_fields) + ", detail_status"
        placeholders = ", ".join(["?"] * len(all_fields)) + ", 'pending'"

        values = [url, flat_dict.get("cian_id")]
        for field in _LISTING_NUMERIC_FIELDS:
            values.append(flat_dict.get(field))
        for field in _LISTING_TEXT_FIELDS:
            values.append(flat_dict.get(field, ""))

        sql = f"INSERT INTO flats ({field_names}) VALUES ({placeholders})"
        conn.execute(sql, values)

    def bulk_upsert_from_listing(
        self,
        flats: list[dict],
    ) -> tuple[int, int]:
        conn = self._get_conn()
        new_count = 0
        updated_count = 0

        try:
            for flat in flats:
                is_new = self.upsert_from_listing(flat, _commit=False)
                if is_new:
                    new_count += 1
                else:
                    updated_count += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return new_count, updated_count

    def get_next_for_detail(
        self,
        max_attempts: int = 3,
        cooldown_minutes: int = 30,
    ) -> Optional[dict]:
        conn = self._get_conn()
        cooldown_time = (
            datetime.now() - timedelta(minutes=cooldown_minutes)
        ).isoformat()

        row = conn.execute("""
            SELECT id, url FROM flats
            WHERE (
                detail_status = 'pending'
                OR (
                    detail_status = 'failed'
                    AND detail_attempts < ?
                    AND (last_attempt_at IS NULL OR last_attempt_at < ?)
                )
            )
            AND url != ''
            ORDER BY
                CASE detail_status
                    WHEN 'pending' THEN 0
                    WHEN 'failed' THEN 1
                END,
                detail_attempts ASC
            LIMIT 1
        """, (max_attempts, cooldown_time)).fetchone()

        if not row:
            return None

        conn.execute("""
            UPDATE flats
            SET detail_status = 'in_progress',
                last_attempt_at = datetime('now')
            WHERE id = ?
        """, (row["id"],))
        conn.commit()

        return {"id": row["id"], "url": row["url"]}

    def update_detail(self, flat_id: int, details: dict) -> None:
        conn = self._get_conn()

        set_clauses = []
        values = []

        for field in DETAIL_FIELDS:
            if field in details and details[field] is not None:
                set_clauses.append(f"{field} = COALESCE(?, {field})")
                val = details[field]
                if isinstance(val, bool):
                    val = int(val)
                values.append(val)

        set_clauses.extend([
            "detail_status = 'done'",
            "detail_attempts = detail_attempts + 1",
            "updated_at = datetime('now')",
        ])

        values.append(flat_id)

        sql = f"UPDATE flats SET {', '.join(set_clauses)} WHERE id = ?"
        conn.execute(sql, values)
        conn.commit()

    def mark_failed(self, flat_id: int) -> None:

        self._update_status(flat_id, DetailStatus.FAILED)

    def mark_blocked(self, flat_id: int) -> None:

        self._update_status(flat_id, DetailStatus.BLOCKED)

    def _update_status(self, flat_id: int, status: DetailStatus) -> None:
        conn = self._get_conn()
        conn.execute("""
            UPDATE flats
            SET detail_status = ?,
                detail_attempts = detail_attempts + 1,
                last_attempt_at = datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (status.value, flat_id))
        conn.commit()

    def reset_blocked(self) -> int:

        conn = self._get_conn()
        cursor = conn.execute("""
            UPDATE flats
            SET detail_status = 'pending'
            WHERE detail_status = 'blocked'
        """)
        conn.commit()
        count = cursor.rowcount
        if count:
            logger.info(f"  Сброшено {count} blocked → pending")
        return count

    def reset_stale_in_progress(
        self,
        timeout_minutes: int = 60,
    ) -> int:

        conn = self._get_conn()
        cutoff = (
            datetime.now() - timedelta(minutes=timeout_minutes)
        ).isoformat()

        cursor = conn.execute("""
            UPDATE flats
            SET detail_status = 'pending'
            WHERE detail_status = 'in_progress'
              AND (last_attempt_at IS NULL OR last_attempt_at < ?)
        """, (cutoff,))
        conn.commit()
        count = cursor.rowcount
        if count:
            logger.info(f"  Сброшено {count} in_progress → pending")
        return count


    def get_stats(self) -> dict:

        conn = self._get_conn()
        rows = conn.execute("""
            SELECT detail_status, COUNT(*) as cnt
            FROM flats
            GROUP BY detail_status
        """).fetchall()

        stats = {row["detail_status"]: row["cnt"] for row in rows}
        stats["total"] = sum(stats.values())


        for status in DetailStatus:
            stats.setdefault(status.value, 0)

        return stats

    def get_coverage(self) -> dict:

        conn = self._get_conn()

        total = conn.execute("SELECT COUNT(*) FROM flats").fetchone()[0]
        if total == 0:
            return {}


        parts = []
        for field in COVERAGE_FIELDS:
            parts.append(
                f"SUM(CASE WHEN {field} IS NOT NULL "
                f"AND {field} != '' "
                f"AND {field} != 0 "
                f"THEN 1 ELSE 0 END) AS {field}"
            )

        sql = f"SELECT {', '.join(parts)} FROM flats"
        row = conn.execute(sql).fetchone()

        coverage = {}
        for i, field in enumerate(COVERAGE_FIELDS):
            filled = row[i] or 0
            coverage[field] = round(filled / total * 100, 1)

        return coverage


    def export_to_csv(self, filepath: str) -> int:

        return self._export(
            filepath,
            "SELECT * FROM flats ORDER BY district, street",
        )

    def export_done_to_csv(self, filepath: str) -> int:

        return self._export(
            filepath,
            "SELECT * FROM flats WHERE detail_status = 'done' "
            "ORDER BY district",
        )

    def _export(self, filepath: str, query: str) -> int:
        conn = self._get_conn()
        df = pd.read_sql_query(query, conn)
        df.to_csv(filepath, index=False, sep=";", encoding="utf-8")
        logger.info(f"  Экспорт: {filepath} ({len(df)} записей)")
        return len(df)


    def close(self) -> None:

        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "FlatStorage":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass