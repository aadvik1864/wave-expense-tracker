"""Local SQLite persistence for Wave. No remote services or account connections."""

from __future__ import annotations

import os
import sqlite3
import calendar
from datetime import date, timedelta
from pathlib import Path
from typing import Any


STARTER_CATEGORIES = [
    ("Groceries", "#57D6B2", "G", "expense"),
    ("Dining & coffee", "#FFB581", "D", "expense"),
    ("Home", "#A9B4FF", "H", "expense"),
    ("Transit", "#65C8E5", "T", "expense"),
    ("Wellness", "#F29AC5", "W", "expense"),
    ("Shopping", "#F4D07D", "S", "expense"),
    ("Fun", "#B7A0FF", "F", "expense"),
    ("Salary", "#66D7B6", "↗", "income"),
    ("Side income", "#83D0F2", "+", "income"),
]

def _data_path() -> Path:
    explicit = os.environ.get("WAVE_DB_PATH")
    if explicit:
        return Path(explicit).expanduser()
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "wave" / "expenses.db"


class Store:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path else _data_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def _initialize(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                color TEXT NOT NULL,
                mark TEXT NOT NULL DEFAULT '•',
                kind TEXT NOT NULL CHECK(kind IN ('expense', 'income'))
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                kind TEXT NOT NULL CHECK(kind IN ('expense', 'income')),
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                happened_on TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_date
                ON transactions(happened_on DESC, id DESC);
            CREATE TABLE IF NOT EXISTS budgets (
                category_id INTEGER PRIMARY KEY REFERENCES categories(id) ON DELETE CASCADE,
                monthly_limit_cents INTEGER NOT NULL CHECK(monthly_limit_cents > 0)
            );
            CREATE TABLE IF NOT EXISTS recurring_entries (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                kind TEXT NOT NULL CHECK(kind IN ('expense', 'income')),
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                frequency TEXT NOT NULL CHECK(frequency IN ('weekly', 'monthly', 'yearly')),
                next_due TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1)),
                anchor_month INTEGER NOT NULL DEFAULT 0,
                anchor_day INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_recurring_due ON recurring_entries(next_due, enabled);
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        self.db.commit()
        recurring_columns = {
            row["name"] for row in self.db.execute("PRAGMA table_info(recurring_entries)")
        }
        if "anchor_month" not in recurring_columns:
            self.db.execute("ALTER TABLE recurring_entries ADD COLUMN anchor_month INTEGER NOT NULL DEFAULT 0")
        if "anchor_day" not in recurring_columns:
            self.db.execute("ALTER TABLE recurring_entries ADD COLUMN anchor_day INTEGER NOT NULL DEFAULT 0")
        self.db.execute(
            """UPDATE recurring_entries
               SET anchor_month = CAST(substr(next_due, 6, 2) AS INTEGER),
                   anchor_day = CAST(substr(next_due, 9, 2) AS INTEGER)
               WHERE anchor_month = 0 OR anchor_day = 0"""
        )
        categories_initialized = self.db.execute(
            "SELECT value FROM app_meta WHERE key = 'starter_categories_initialized'"
        ).fetchone()
        if not categories_initialized:
            if self.db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
                self.db.executemany(
                    "INSERT INTO categories(name, color, mark, kind) VALUES (?, ?, ?, ?)",
                    STARTER_CATEGORIES,
                )
            self.db.execute(
                "INSERT INTO app_meta(key, value) VALUES ('starter_categories_initialized', '1')"
            )
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def categories(self, kind: str | None = None) -> list[dict[str, Any]]:
        if kind:
            rows = self.db.execute(
                "SELECT * FROM categories WHERE kind = ? ORDER BY name COLLATE NOCASE", (kind,)
            )
        else:
            rows = self.db.execute("SELECT * FROM categories ORDER BY kind, name COLLATE NOCASE")
        return [dict(row) for row in rows]

    def add_category(self, name: str, color: str, mark: str, kind: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO categories(name, color, mark, kind) VALUES (?, ?, ?, ?)",
            (name.strip(), color, mark.strip() or name[:1].upper(), kind),
        )
        self.db.commit()
        return int(cursor.lastrowid)

    def rename_category(self, category_id: int, name: str) -> None:
        self.db.execute("UPDATE categories SET name = ? WHERE id = ?", (name.strip(), category_id))
        self.db.commit()

    def delete_category(self, category_id: int) -> bool:
        used = self.db.execute(
            "SELECT COUNT(*) FROM transactions WHERE category_id = ?", (category_id,)
        ).fetchone()[0]
        scheduled = self.db.execute(
            "SELECT COUNT(*) FROM recurring_entries WHERE category_id = ?", (category_id,)
        ).fetchone()[0]
        if used or scheduled:
            return False
        self.db.execute("DELETE FROM budgets WHERE category_id = ?", (category_id,))
        self.db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.db.commit()
        return True

    def save_budget(self, category_id: int, limit_cents: int) -> None:
        self.db.execute(
            """INSERT INTO budgets(category_id, monthly_limit_cents) VALUES (?, ?)
               ON CONFLICT(category_id) DO UPDATE SET monthly_limit_cents = excluded.monthly_limit_cents""",
            (category_id, limit_cents),
        )
        self.db.commit()

    def preference(self, key: str) -> str | None:
        row = self.db.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
        return str(row[0]) if row else None

    def set_preference(self, key: str, value: str) -> None:
        self.db.execute(
            """INSERT INTO app_meta(key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, value),
        )
        self.db.commit()

    def budget_rows(self, month: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            """SELECT c.id, c.name, c.color, c.mark,
                      COALESCE(b.monthly_limit_cents, 0) AS limit_cents,
                      COALESCE(SUM(t.amount_cents), 0) AS spent_cents
               FROM categories c
               LEFT JOIN budgets b ON b.category_id = c.id
               LEFT JOIN transactions t ON t.category_id = c.id AND t.kind = 'expense'
                   AND substr(t.happened_on, 1, 7) = ?
               WHERE c.kind = 'expense'
               GROUP BY c.id, b.monthly_limit_cents
               ORDER BY CASE WHEN b.monthly_limit_cents IS NULL THEN 1 ELSE 0 END,
                        c.name COLLATE NOCASE""",
            (month,),
        )
        return [dict(row) for row in rows]

    def month_totals(self, month: str) -> dict[str, int]:
        rows = self.db.execute(
            """SELECT kind, COALESCE(SUM(amount_cents), 0) AS total
               FROM transactions WHERE substr(happened_on, 1, 7) = ? GROUP BY kind""",
            (month,),
        )
        totals = {row["kind"]: int(row["total"]) for row in rows}
        return {"expense": totals.get("expense", 0), "income": totals.get("income", 0)}

    def daily_spend(self, month: str, days_in_month: int) -> list[int]:
        values = [0] * days_in_month
        rows = self.db.execute(
            """SELECT CAST(substr(happened_on, 9, 2) AS INTEGER) AS day,
                      SUM(amount_cents) AS total
               FROM transactions WHERE kind = 'expense' AND substr(happened_on, 1, 7) = ?
               GROUP BY day""",
            (month,),
        )
        for row in rows:
            if 1 <= row["day"] <= days_in_month:
                values[row["day"] - 1] = int(row["total"])
        return values

    def transactions(
        self,
        month: str | None = None,
        search: str = "",
        category_id: int | None = None,
        kind: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if month:
            clauses.append("substr(t.happened_on, 1, 7) = ?")
            params.append(month)
        if search.strip():
            clauses.append("(t.title LIKE ? OR t.note LIKE ? OR c.name LIKE ?)")
            token = f"%{search.strip()}%"
            params.extend([token, token, token])
        if category_id is not None:
            clauses.append("t.category_id = ?")
            params.append(category_id)
        if kind:
            clauses.append("t.kind = ?")
            params.append(kind)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.db.execute(
            f"""SELECT t.*, c.name AS category_name, c.color AS category_color,
                       c.mark AS category_mark
                FROM transactions t JOIN categories c ON c.id = t.category_id
                {where} ORDER BY t.happened_on DESC, t.id DESC""",
            params,
        )
        return [dict(row) for row in rows]

    def add_transaction(
        self,
        title: str,
        amount_cents: int,
        kind: str,
        category_id: int,
        happened_on: str,
        note: str = "",
    ) -> None:
        self.db.execute(
            """INSERT INTO transactions(title, amount_cents, kind, category_id, happened_on, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title.strip(), amount_cents, kind, category_id, happened_on, note.strip()),
        )
        self.set_preference(f"last_category_{kind}", str(category_id))
        self.db.commit()

    def update_transaction(
        self,
        transaction_id: int,
        title: str,
        amount_cents: int,
        kind: str,
        category_id: int,
        happened_on: str,
        note: str = "",
    ) -> None:
        self.db.execute(
            """UPDATE transactions
               SET title = ?, amount_cents = ?, kind = ?, category_id = ?, happened_on = ?, note = ?
               WHERE id = ?""",
            (title.strip(), amount_cents, kind, category_id, happened_on, note.strip(), transaction_id),
        )
        self.set_preference(f"last_category_{kind}", str(category_id))
        self.db.commit()

    def delete_transaction(self, transaction_id: int) -> None:
        self.db.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        self.db.commit()

    def recurring_entries(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        where = "WHERE r.enabled = 1" if enabled_only else ""
        rows = self.db.execute(
            f"""SELECT r.*, c.name AS category_name, c.color AS category_color,
                       c.mark AS category_mark
                FROM recurring_entries r JOIN categories c ON c.id = r.category_id
                {where} ORDER BY r.next_due, r.title COLLATE NOCASE"""
        )
        return [dict(row) for row in rows]

    def due_recurring(self, as_of: date | None = None) -> list[dict[str, Any]]:
        cutoff = (as_of or date.today()).isoformat()
        rows = self.db.execute(
            """SELECT r.*, c.name AS category_name, c.color AS category_color,
                      c.mark AS category_mark
               FROM recurring_entries r JOIN categories c ON c.id = r.category_id
               WHERE r.enabled = 1 AND r.next_due <= ?
               ORDER BY r.next_due, r.title COLLATE NOCASE""",
            (cutoff,),
        )
        return [dict(row) for row in rows]

    def add_recurring(
        self,
        title: str,
        amount_cents: int,
        kind: str,
        category_id: int,
        frequency: str,
        next_due: str,
        note: str = "",
    ) -> int:
        cursor = self.db.execute(
            """INSERT INTO recurring_entries
               (title, amount_cents, kind, category_id, frequency, next_due, note, anchor_month, anchor_day)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title.strip(), amount_cents, kind, category_id, frequency, next_due, note.strip(),
                date.fromisoformat(next_due).month, date.fromisoformat(next_due).day,
            ),
        )
        self.db.commit()
        return int(cursor.lastrowid)

    def update_recurring(
        self,
        recurring_id: int,
        title: str,
        amount_cents: int,
        kind: str,
        category_id: int,
        frequency: str,
        next_due: str,
        note: str = "",
    ) -> None:
        self.db.execute(
            """UPDATE recurring_entries
               SET title = ?, amount_cents = ?, kind = ?, category_id = ?,
                   frequency = ?, next_due = ?, note = ?, anchor_month = ?, anchor_day = ?
               WHERE id = ?""",
            (
                title.strip(), amount_cents, kind, category_id, frequency, next_due, note.strip(),
                date.fromisoformat(next_due).month, date.fromisoformat(next_due).day, recurring_id,
            ),
        )
        self.db.commit()

    def delete_recurring(self, recurring_id: int) -> None:
        self.db.execute("DELETE FROM recurring_entries WHERE id = ?", (recurring_id,))
        self.db.commit()

    @staticmethod
    def _next_occurrence(
        current: date,
        frequency: str,
        anchor_month: int | None = None,
        anchor_day: int | None = None,
    ) -> date:
        if frequency == "weekly":
            return current + timedelta(days=7)
        if frequency == "monthly":
            year = current.year + (current.month == 12)
            month = current.month % 12 + 1
            day = anchor_day or current.day
            return date(year, month, min(day, calendar.monthrange(year, month)[1]))
        if frequency == "yearly":
            year = current.year + 1
            month = anchor_month or current.month
            day = anchor_day or current.day
            return date(year, month, min(day, calendar.monthrange(year, month)[1]))
        raise ValueError(f"Unsupported recurrence frequency: {frequency}")

    def post_recurring(self, recurring_id: int) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT * FROM recurring_entries WHERE id = ? AND enabled = 1", (recurring_id,)
            ).fetchone()
            if row is None:
                raise ValueError("This recurring entry is no longer active.")
            due_date = date.fromisoformat(row["next_due"])
            self.db.execute(
                """INSERT INTO transactions
                   (title, amount_cents, kind, category_id, happened_on, note)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (row["title"], row["amount_cents"], row["kind"], row["category_id"], row["next_due"], row["note"]),
            )
            next_due = self._next_occurrence(
                due_date, row["frequency"], row["anchor_month"], row["anchor_day"]
            )
            self.db.execute(
                "UPDATE recurring_entries SET next_due = ? WHERE id = ?",
                (next_due.isoformat(), recurring_id),
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def skip_recurring(self, recurring_id: int) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT frequency, next_due, anchor_month, anchor_day FROM recurring_entries WHERE id = ? AND enabled = 1",
                (recurring_id,),
            ).fetchone()
            if row is None:
                raise ValueError("This recurring entry is no longer active.")
            next_due = self._next_occurrence(
                date.fromisoformat(row["next_due"]), row["frequency"], row["anchor_month"], row["anchor_day"]
            )
            self.db.execute(
                "UPDATE recurring_entries SET next_due = ? WHERE id = ?",
                (next_due.isoformat(), recurring_id),
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def export_backup(self, path: str | Path) -> None:
        target = Path(path).expanduser().resolve()
        if target == self.path.resolve():
            raise ValueError("Choose a different location from the live Wave database.")
        target.parent.mkdir(parents=True, exist_ok=True)
        destination = sqlite3.connect(target)
        try:
            self.db.backup(destination)
        finally:
            destination.close()

    def restore_backup(self, path: str | Path) -> None:
        source_path = Path(path).expanduser().resolve()
        if source_path == self.path.resolve():
            raise ValueError("Choose a backup file, not the live Wave database.")
        if not source_path.is_file():
            raise FileNotFoundError(source_path)

        source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
        try:
            integrity = source.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise ValueError("This backup failed its SQLite integrity check.")
            required = {"categories", "transactions", "budgets", "recurring_entries", "app_meta"}
            available = {
                row[0]
                for row in source.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            if not required.issubset(available):
                raise ValueError("This file is not a complete Wave backup.")
            if source.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("This backup contains broken category references.")
        finally:
            source.close()

        self.db.execute("ATTACH DATABASE ? AS restore_source", (str(source_path),))
        try:
            self.db.execute("BEGIN IMMEDIATE")
            for table in ("transactions", "recurring_entries", "budgets", "categories", "app_meta"):
                self.db.execute(f"DELETE FROM main.{table}")
            copies = {
                "categories": "id, name, color, mark, kind",
                "transactions": "id, title, amount_cents, kind, category_id, happened_on, note",
                "budgets": "category_id, monthly_limit_cents",
                "recurring_entries": "id, title, amount_cents, kind, category_id, frequency, next_due, note, enabled, anchor_month, anchor_day",
                "app_meta": "key, value",
            }
            for table, columns in copies.items():
                self.db.execute(
                    f"INSERT INTO main.{table} ({columns}) SELECT {columns} FROM restore_source.{table}"
                )
            if self.db.execute("PRAGMA main.foreign_key_check").fetchone():
                raise ValueError("The backup does not match this Wave database version.")
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        finally:
            self.db.execute("DETACH DATABASE restore_source")
