"""Unit tests for the SQLite repository and the sample data (temporary database per test)."""

import sqlite3
from pathlib import Path

import pytest

from app.database import init_schema, open_database
from app.repository import PollRepository
from app.sample_data import seed_sample_data


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    connection = open_database(tmp_path / "test.db")
    init_schema(connection)
    yield connection
    connection.close()


def test_insert_and_read_poll_with_options(conn: sqlite3.Connection) -> None:
    repo = PollRepository(conn)
    poll_id = repo.insert_poll("Q?", "desc", "2026-01-01T00:00:00+00:00")
    option_id = repo.insert_option(poll_id, "A", 1)
    repo.insert_option(poll_id, "B", 2)
    assert repo.get_poll(poll_id)["question"] == "Q?"
    assert repo.get_poll(999) is None
    assert [o["label"] for o in repo.list_options(poll_id)] == ["A", "B"]
    assert repo.get_option(option_id)["poll_id"] == poll_id
    assert repo.list_polls()[0]["option_count"] == 2


def test_insert_vote_refuses_second_vote_by_same_voter(conn: sqlite3.Connection) -> None:
    repo = PollRepository(conn)
    poll_id = repo.insert_poll("Q?", "", "t")
    a = repo.insert_option(poll_id, "A", 1)
    b = repo.insert_option(poll_id, "B", 2)
    voter = "a" * 32
    assert repo.insert_vote(poll_id, a, voter, "t") is True
    assert repo.insert_vote(poll_id, b, voter, "t") is False
    assert repo.count_votes_by_option(poll_id) == {a: 1}


def test_seed_sample_data_only_when_empty(conn: sqlite3.Connection) -> None:
    assert seed_sample_data(conn) is True
    repo = PollRepository(conn)
    assert repo.count_polls() == 3
    assert seed_sample_data(conn) is False
    assert repo.count_polls() == 3
