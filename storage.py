from __future__ import annotations
import json
import sqlite3
from datetime import date
from pathlib import Path

from filter import Paper, ScoredPaper

DB_PATH = Path.home() / ".paperbot" / "seen.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id             TEXT PRIMARY KEY,
    seen_date      TEXT NOT NULL,
    title          TEXT,
    abstract       TEXT,
    authors        TEXT,
    url            TEXT,
    source         TEXT,
    score          INTEGER,
    matched_groups TEXT,
    matched_terms  TEXT,
    matched_authors TEXT
);
"""


class PaperStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)
        self.conn.commit()
        # Migration: add matched_authors column to databases created before this feature
        try:
            self.conn.execute("ALTER TABLE papers ADD COLUMN matched_authors TEXT DEFAULT '[]'")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    def is_seen(self, paper_id: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM papers WHERE id = ?", (paper_id,))
        return cur.fetchone() is not None

    def save(self, sp: ScoredPaper) -> None:
        p = sp.paper
        with self.conn:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO papers
                    (id, seen_date, title, abstract, authors, url, source,
                     score, matched_groups, matched_terms, matched_authors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p.id,
                    date.today().isoformat(),
                    p.title,
                    p.abstract,
                    json.dumps(p.authors),
                    p.url,
                    p.source,
                    sp.score,
                    json.dumps(sp.matched_groups),
                    json.dumps(sp.matched_terms),
                    json.dumps(sp.matched_authors),
                ),
            )

    def get_since(self, date_str: str) -> list[ScoredPaper]:
        cur = self.conn.execute(
            "SELECT * FROM papers WHERE seen_date >= ? ORDER BY score DESC, source",
            (date_str,),
        )
        results = []
        for row in cur.fetchall():
            p = Paper(
                id=row["id"],
                title=row["title"] or "",
                abstract=row["abstract"] or "",
                authors=json.loads(row["authors"] or "[]"),
                url=row["url"] or "",
                source=row["source"] or "",
                date=row["seen_date"],
            )
            results.append(
                ScoredPaper(
                    paper=p,
                    score=row["score"] or 0,
                    matched_groups=json.loads(row["matched_groups"] or "[]"),
                    matched_terms=json.loads(row["matched_terms"] or "[]"),
                    matched_authors=json.loads(row["matched_authors"] or "[]"),
                )
            )
        return results

    def clear(self) -> None:
        self.conn.executescript("DROP TABLE IF EXISTS papers;")
        self.conn.commit()
        self._init_schema()

    def close(self) -> None:
        self.conn.close()
