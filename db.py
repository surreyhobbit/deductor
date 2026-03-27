import os
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "/data/pocket.db")

# ── Configuration ──────────────────────────────────────────────────────────────
# Edit names and monthly allowances (CHF) here.
CHILDREN = [
    {"id": 1, "name": "Mia",   "allowance_chf": 20},
    {"id": 2, "name": "Noah",  "allowance_chf": 15},
]


def _connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _connect() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS children (
                id            INTEGER PRIMARY KEY,
                name          TEXT    NOT NULL,
                allowance_chf INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS monthly_summary (
                id          INTEGER PRIMARY KEY,
                child_id    INTEGER NOT NULL REFERENCES children(id),
                year        INTEGER NOT NULL,
                month       INTEGER NOT NULL,
                base_amount INTEGER NOT NULL,
                UNIQUE(child_id, year, month)
            );

            CREATE TABLE IF NOT EXISTS deductions (
                id          INTEGER PRIMARY KEY,
                child_id    INTEGER NOT NULL REFERENCES children(id),
                year        INTEGER NOT NULL,
                month       INTEGER NOT NULL,
                deducted_at TEXT    NOT NULL,
                amount_chf  INTEGER NOT NULL DEFAULT 1
            );
        """)
        # Seed / update children config
        for c in CHILDREN:
            con.execute("""
                INSERT INTO children (id, name, allowance_chf)
                VALUES (:id, :name, :allowance_chf)
                ON CONFLICT(id) DO UPDATE SET
                    name          = excluded.name,
                    allowance_chf = excluded.allowance_chf
            """, c)


def ensure_month(child_id: int, year: int, month: int):
    """Create monthly_summary row for this child/month if it doesn't exist."""
    with _connect() as con:
        row = con.execute(
            "SELECT allowance_chf FROM children WHERE id = ?", (child_id,)
        ).fetchone()
        if row:
            con.execute("""
                INSERT OR IGNORE INTO monthly_summary
                    (child_id, year, month, base_amount)
                VALUES (?, ?, ?, ?)
            """, (child_id, year, month, row["allowance_chf"]))


def get_summary(year: int, month: int) -> list[dict]:
    """Return current-month summary for all children."""
    results = []
    with _connect() as con:
        for c in CHILDREN:
            ensure_month(c["id"], year, month)
            row = con.execute("""
                SELECT ms.base_amount,
                       COALESCE(SUM(d.amount_chf), 0) AS total_deducted
                FROM monthly_summary ms
                LEFT JOIN deductions d
                       ON d.child_id = ms.child_id
                      AND d.year     = ms.year
                      AND d.month    = ms.month
                WHERE ms.child_id = ? AND ms.year = ? AND ms.month = ?
                GROUP BY ms.id
            """, (c["id"], year, month)).fetchone()

            # Recent deduction log (newest first, max 20)
            log = con.execute("""
                SELECT deducted_at, amount_chf
                FROM deductions
                WHERE child_id = ? AND year = ? AND month = ?
                ORDER BY deducted_at DESC
                LIMIT 20
            """, (c["id"], year, month)).fetchall()

            base      = row["base_amount"]
            deducted  = row["total_deducted"]
            remaining = base - deducted

            results.append({
                "id":        c["id"],
                "name":      c["name"],
                "base":      base,
                "deducted":  deducted,
                "remaining": remaining,
                "log":       [dict(r) for r in log],
            })
    return results


def add_deduction(child_id: int, year: int, month: int):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with _connect() as con:
        con.execute("""
            INSERT INTO deductions (child_id, year, month, deducted_at, amount_chf)
            VALUES (?, ?, ?, ?, 1)
        """, (child_id, year, month, ts))


def get_history() -> list[dict]:
    """Monthly totals per child, all time, newest first."""
    with _connect() as con:
        rows = con.execute("""
            SELECT c.name,
                   ms.year,
                   ms.month,
                   ms.base_amount,
                   COALESCE(SUM(d.amount_chf), 0) AS total_deducted,
                   ms.base_amount - COALESCE(SUM(d.amount_chf), 0) AS remaining
            FROM monthly_summary ms
            JOIN children c ON c.id = ms.child_id
            LEFT JOIN deductions d
                   ON d.child_id = ms.child_id
                  AND d.year     = ms.year
                  AND d.month    = ms.month
            GROUP BY ms.id
            ORDER BY ms.year DESC, ms.month DESC, c.name
        """).fetchall()
    return [dict(r) for r in rows]
