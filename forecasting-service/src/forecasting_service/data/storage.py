import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger


class DetailStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


DB_DIR = Path(__file__).resolve().parent.parent / "datasets"


class FlatStorage:

    def __init__(self, db_name: str = "flats.db"):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = DB_DIR / db_name
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path), timeout=30,
            )
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
        logger.info(f" БД инициализирована: {self.db_path}")

    def upsert_from_listing(self, flat_dict: dict) -> bool:
        conn = self._get_conn()
        url = flat_dict.get("url", "")
        if not url:
            return False

        existing = conn.execute(
            "SELECT id, detail_status FROM flats WHERE url = ?",
            (url,),
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE flats SET
                    price = COALESCE(?, price),
                    total_meters = COALESCE(?, total_meters),
                    rooms_count = COALESCE(?, rooms_count),
                    floor = COALESCE(?, floor),
                    floors_count = COALESCE(?, floors_count),
                    district = CASE WHEN ? != '' THEN ? ELSE district END,
                    microdistrict = CASE WHEN ? != '' THEN ? ELSE microdistrict END,
                    street = CASE WHEN ? != '' THEN ? ELSE street END,
                    house_number = CASE WHEN ? != '' THEN ? ELSE house_number END,
                    residential_complex = CASE WHEN ? != '' THEN ? ELSE residential_complex END,
                    underground = CASE WHEN ? != '' THEN ? ELSE underground END,
                    address_raw = CASE WHEN ? != '' THEN ? ELSE address_raw END,
                    title_raw = CASE WHEN ? != '' THEN ? ELSE title_raw END,
                    updated_at = datetime('now')
                WHERE url = ?
            """, (
                flat_dict.get("price"),
                flat_dict.get("total_meters"),
                flat_dict.get("rooms_count"),
                flat_dict.get("floor"),
                flat_dict.get("floors_count"),
                flat_dict.get("district", ""), flat_dict.get("district", ""),
                flat_dict.get("microdistrict", ""), flat_dict.get("microdistrict", ""),
                flat_dict.get("street", ""), flat_dict.get("street", ""),
                flat_dict.get("house_number", ""), flat_dict.get("house_number", ""),
                flat_dict.get("residential_complex", ""), flat_dict.get("residential_complex", ""),
                flat_dict.get("underground", ""), flat_dict.get("underground", ""),
                flat_dict.get("address_raw", ""), flat_dict.get("address_raw", ""),
                flat_dict.get("title_raw", ""), flat_dict.get("title_raw", ""),
                url,
            ))
            conn.commit()
            return False

        conn.execute("""
            INSERT INTO flats (
                url, cian_id, price,
                total_meters, rooms_count, floor, floors_count,
                district, microdistrict,
                street, house_number, underground,
                residential_complex, address_raw, title_raw,
                detail_status
            ) VALUES (


                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                'pending'
            )
        """, (
            url,
            flat_dict.get("cian_id"),
            flat_dict.get("price"),
            flat_dict.get("total_meters"),
            flat_dict.get("rooms_count"),
            flat_dict.get("floor"),
            flat_dict.get("floors_count"),
            flat_dict.get("district", ""),
            flat_dict.get("microdistrict", ""),
            flat_dict.get("street", ""),
            flat_dict.get("house_number", ""),
            flat_dict.get("underground", ""),
            flat_dict.get("residential_complex", ""),
            flat_dict.get("address_raw", ""),
            flat_dict.get("title_raw", ""),
        ))
        conn.commit()
        return True

    def bulk_upsert_from_listing(
        self, flats: list[dict]
    ) -> tuple[int, int]:
        new_count = 0
        updated_count = 0
        for flat in flats:
            is_new = self.upsert_from_listing(flat)
            if is_new:
                new_count += 1
            else:
                updated_count += 1
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
            SELECT * FROM flats
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

        if row:
            conn.execute("""
                UPDATE flats
                SET detail_status = 'in_progress',
                    last_attempt_at = datetime('now')
                WHERE id = ?
            """, (row["id"],))
            conn.commit()
            return dict(row)

        return None

    def update_detail(self, flat_id: int, details: dict) -> None:
        conn = self._get_conn()

        detail_fields = [
            "living_meters", "kitchen_meters", "ceiling_height",
            "object_type", "layout_type",
            "bathroom_type", "bathroom_count",
            "window_view", "finish_type",
            "balcony_count", "loggia_count", "has_furniture",
            "year_of_construction", "house_material_type",
            "floor_type",
            "elevator_passenger", "elevator_cargo",
            "entrances_count",
            "has_garbage_chute", "has_ramp", "has_concierge",
            "parking_type", "heating_type", "is_emergency",
            "jk_name", "jk_class", "jk_deadline", "developer",
            "cadastral_number", "encumbrances", "owners_count",
        ]

        set_clauses = []
        values = []
        for field in detail_fields:
            if field in details and details[field] is not None:
                set_clauses.append(f"{field} = COALESCE(?, {field})")
                val = details[field]
                if isinstance(val, bool):
                    val = int(val)
                values.append(val)

        set_clauses.append("detail_status = 'done'")
        set_clauses.append("detail_attempts = detail_attempts + 1")
        set_clauses.append("updated_at = datetime('now')")

        values.append(flat_id)

        sql = f"UPDATE flats SET {', '.join(set_clauses)} WHERE id = ?"
        conn.execute(sql, values)
        conn.commit()



    def mark_failed(self, flat_id: int) -> None:
        conn = self._get_conn()
        conn.execute("""
            UPDATE flats
            SET detail_status = 'failed',
                detail_attempts = detail_attempts + 1,
                last_attempt_at = datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (flat_id,))
        conn.commit()

    def mark_blocked(self, flat_id: int) -> None:
        conn = self._get_conn()
        conn.execute("""
            UPDATE flats
            SET detail_status = 'blocked',
                detail_attempts = detail_attempts + 1,
                last_attempt_at = datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (flat_id,))
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
            logger.info(f" Сброшено {count} blocked → pending")
        return count

    def get_stats(self) -> dict:
        conn = self._get_conn()
        stats = {}
        stats["total"] = conn.execute(
            "SELECT COUNT(*) FROM flats"
        ).fetchone()[0]

        for status in DetailStatus:
            stats[status.value] = conn.execute(
                "SELECT COUNT(*) FROM flats WHERE detail_status = ?",
                (status.value,),
            ).fetchone()[0]

        return stats

    def get_coverage(self) -> dict:
        conn = self._get_conn()
        total = conn.execute(
            "SELECT COUNT(*) FROM flats"
        ).fetchone()[0]

        if total == 0:


            return {}

        fields = [
            "price", "total_meters", "rooms_count",
            "floor", "floors_count", "district",
            "microdistrict", "street", "house_number",
            "living_meters", "kitchen_meters",
            "ceiling_height", "object_type",
            "year_of_construction", "house_material_type",
            "finish_type", "bathroom_type", "bathroom_count",
            "elevator_passenger", "elevator_cargo",
            "parking_type", "floor_type",
            "heating_type", "balcony_count",
            "loggia_count", "window_view",
            "layout_type", "has_furniture",
        ]

        coverage = {}
        for field in fields:
            filled = conn.execute(f"""
                SELECT COUNT(*) FROM flats
                WHERE {field} IS NOT NULL
                AND {field} != ''
                AND {field} != 0
            """).fetchone()[0]
            coverage[field] = round(filled / total * 100, 1)

        return coverage

    def export_to_csv(self, filepath: str) -> None:
        conn = self._get_conn()
        df = pd.read_sql_query(
            "SELECT * FROM flats ORDER BY district, street",
            conn,
        )
        df.to_csv(filepath, index=False, sep=";", encoding="utf-8")
        logger.info(f" Экспорт: {filepath} ({len(df)} записей)")

    def export_done_to_csv(self, filepath: str) -> None:
        conn = self._get_conn()
        df = pd.read_sql_query(
            "SELECT * FROM flats WHERE detail_status = 'done' ORDER BY district",
            conn,
        )
        df.to_csv(filepath, index=False, sep=";", encoding="utf-8")
        logger.info(f" Экспорт (done): {filepath} ({len(df)} записей)")

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None