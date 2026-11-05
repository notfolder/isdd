"""SQLite による保存処理: 投票テーマ・選択肢・投票の読み書きと集計。"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional

SAMPLE_POLLS = [
    {
        "question": "Which programming language do you like most?",
        "description": "Pick the one you use the most.",
        "options": [("Python", 4), ("JavaScript", 3), ("Go", 1), ("Rust", 2)],
    },
    {
        "question": "What is your favorite season?",
        "description": "Choose the season you enjoy most.",
        "options": [("Spring", 2), ("Summer", 5), ("Autumn", 3), ("Winter", 1)],
    },
    {
        "question": "Which feature would you like to see next?",
        "description": "Your choice helps us decide what to build.",
        "options": [("Dark mode", 6), ("Export to CSV", 2), ("Offline access", 3)],
    },
]


def _connect(db_path: str) -> sqlite3.Connection:
    """外部キーを有効にして接続する。"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _now() -> str:
    """投票日時（UTC、ISO 8601 形式）を返す。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_options(conn: sqlite3.Connection, poll_id: int) -> List[Dict]:
    """投票テーマの選択肢ごとに票数と割合を集計して返す。"""
    rows = conn.execute(
        """
        SELECT o.id, o.text, COUNT(v.id) AS votes
        FROM poll_options AS o
        LEFT JOIN votes AS v ON v.option_id = o.id
        WHERE o.poll_id = ?
        GROUP BY o.id
        ORDER BY o.id
        """,
        (poll_id,),
    ).fetchall()
    total = sum(row["votes"] for row in rows)
    options = []
    for row in rows:
        percent = round(row["votes"] * 100.0 / total, 1) if total else 0.0
        options.append(
            {"id": row["id"], "text": row["text"], "votes": row["votes"], "percent": percent}
        )
    return options


def init_db(db_path: str) -> None:
    """保存先のディレクトリとテーブルを作る（無ければ）。"""
    folder = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(folder, exist_ok=True)
    conn = _connect(db_path)
    try:
        with conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    description TEXT
                );
                CREATE TABLE IF NOT EXISTS poll_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poll_id INTEGER NOT NULL REFERENCES polls(id),
                    text TEXT NOT NULL,
                    UNIQUE (poll_id, text)
                );
                CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poll_id INTEGER NOT NULL REFERENCES polls(id),
                    option_id INTEGER NOT NULL REFERENCES poll_options(id),
                    voted_at TEXT NOT NULL
                );
                """
            )
    finally:
        conn.close()


def seed_sample_polls(db_path: str) -> None:
    """投票テーマが 1 件も無いときだけ、サンプルの投票テーマと票を入れる。"""
    conn = _connect(db_path)
    try:
        with conn:
            count = conn.execute("SELECT COUNT(*) FROM polls").fetchone()[0]
            if count:
                return
            for sample in SAMPLE_POLLS:
                poll_id = conn.execute(
                    "INSERT INTO polls (question, description) VALUES (?, ?)",
                    (sample["question"], sample["description"]),
                ).lastrowid
                for text, votes in sample["options"]:
                    option_id = conn.execute(
                        "INSERT INTO poll_options (poll_id, text) VALUES (?, ?)",
                        (poll_id, text),
                    ).lastrowid
                    for _ in range(votes):
                        conn.execute(
                            "INSERT INTO votes (poll_id, option_id, voted_at) VALUES (?, ?, ?)",
                            (poll_id, option_id, _now()),
                        )
    finally:
        conn.close()


def list_polls(db_path: str) -> List[Dict]:
    """全投票テーマを返す。各テーマに総票数と、一番多い選択肢の名前を含める。"""
    conn = _connect(db_path)
    try:
        polls = conn.execute("SELECT id, question FROM polls ORDER BY id").fetchall()
        result = []
        for poll in polls:
            options = _load_options(conn, poll["id"])
            total = sum(option["votes"] for option in options)
            leader = None
            if total:
                leader = max(options, key=lambda option: option["votes"])["text"]
            result.append(
                {
                    "id": poll["id"],
                    "question": poll["question"],
                    "option_count": len(options),
                    "total": total,
                    "leader": leader,
                }
            )
        return result
    finally:
        conn.close()


def get_poll(db_path: str, poll_id: int) -> Optional[Dict]:
    """投票テーマ 1 件と、選択肢ごとの票数・割合・総票数を返す。無ければ None。"""
    conn = _connect(db_path)
    try:
        poll = conn.execute(
            "SELECT id, question, description FROM polls WHERE id = ?", (poll_id,)
        ).fetchone()
        if poll is None:
            return None
        options = _load_options(conn, poll_id)
        return {
            "id": poll["id"],
            "question": poll["question"],
            "description": poll["description"],
            "total": sum(option["votes"] for option in options),
            "options": options,
        }
    finally:
        conn.close()


def cast_vote(db_path: str, poll_id: int, option_id: int) -> None:
    """選択肢が投票テーマに属することを確かめてから 1 票を記録する。属さなければ ValueError。"""
    conn = _connect(db_path)
    try:
        with conn:
            belongs = conn.execute(
                "SELECT 1 FROM poll_options WHERE id = ? AND poll_id = ?",
                (option_id, poll_id),
            ).fetchone()
            if belongs is None:
                raise ValueError("option does not belong to this poll")
            conn.execute(
                "INSERT INTO votes (poll_id, option_id, voted_at) VALUES (?, ?, ?)",
                (poll_id, option_id, _now()),
            )
    finally:
        conn.close()
