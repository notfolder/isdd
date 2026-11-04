"""Unit tests for the voting rules and result calculation (temporary database per test)."""

import sqlite3
from pathlib import Path

import pytest

from app.database import init_schema, open_database
from app.repository import PollRepository
from app.voting import InvalidVote, PollNotFound, VotingService

VOTED_AT = "2026-01-01T00:00:00+00:00"


@pytest.fixture
def setup_data(tmp_path: Path):
    conn = open_database(tmp_path / "vote.db")
    init_schema(conn)
    repo = PollRepository(conn)
    poll1 = repo.insert_poll("First?", "", VOTED_AT)
    p1a = repo.insert_option(poll1, "A", 1)
    p1b = repo.insert_option(poll1, "B", 2)
    poll2 = repo.insert_poll("Second?", "", VOTED_AT)
    p2a = repo.insert_option(poll2, "X", 1)
    yield conn, poll1, p1a, p1b, poll2, p2a
    conn.close()


def test_cast_vote_records_and_second_vote_is_ignored(setup_data) -> None:
    conn, poll1, a, b, _poll2, _x = setup_data
    service = VotingService(conn)
    voter = "b" * 32
    assert service.cast_vote(poll1, a, voter, VOTED_AT) == "recorded"
    assert service.cast_vote(poll1, b, voter, VOTED_AT) == "already_voted"
    result = service.get_poll_result(poll1)
    assert result["total"] == 1
    assert [o["votes"] for o in result["options"]] == [1, 0]


def test_missing_option_is_rejected_without_recording(setup_data) -> None:
    conn, poll1, _a, _b, _poll2, _x = setup_data
    with pytest.raises(InvalidVote) as err:
        VotingService(conn).cast_vote(poll1, None, "c" * 32, VOTED_AT)
    assert err.value.message == "Please choose an option."
    assert VotingService(conn).get_poll_result(poll1)["total"] == 0


def test_option_of_another_poll_is_rejected(setup_data) -> None:
    conn, poll1, _a, _b, _poll2, x = setup_data
    with pytest.raises(InvalidVote) as err:
        VotingService(conn).cast_vote(poll1, x, "d" * 32, VOTED_AT)
    assert err.value.message == "That option is not part of this poll."


def test_unknown_poll_raises_not_found(setup_data) -> None:
    conn, *_ = setup_data
    with pytest.raises(PollNotFound):
        VotingService(conn).cast_vote(12345, 1, "e" * 32, VOTED_AT)


def test_percentages_and_empty_poll(setup_data) -> None:
    conn, poll1, a, b, poll2, _x = setup_data
    service = VotingService(conn)
    assert service.get_poll_result(poll2)["options"][0]["percent"] == 0
    assert service.get_poll_result(poll2)["total"] == 0
    service.cast_vote(poll1, a, "1" * 32, VOTED_AT)
    service.cast_vote(poll1, a, "2" * 32, VOTED_AT)
    service.cast_vote(poll1, b, "3" * 32, VOTED_AT)
    result = service.get_poll_result(poll1)
    assert [o["percent"] for o in result["options"]] == [67, 33]
    assert len(service.get_all_results()) == 2
