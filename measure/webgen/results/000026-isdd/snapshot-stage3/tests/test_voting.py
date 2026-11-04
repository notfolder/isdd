"""Unit tests for the voting rules and result calculation (temporary database per test)."""

import sqlite3
from pathlib import Path

import pytest

from app.database import init_schema, open_database
from app.repository import PollRepository
from app.voting import InvalidPoll, InvalidVote, PollNotFound, VotingService

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


def test_create_poll_stores_question_and_options_in_order(setup_data) -> None:
    conn, *_ = setup_data
    service = VotingService(conn)
    poll_id = service.create_poll("  Best fruit?  ", ["Apple", "", "  Pear ", "Plum"], VOTED_AT)
    poll = PollRepository(conn).get_poll(poll_id)
    assert poll["question"] == "Best fruit?"
    options = PollRepository(conn).list_options(poll_id)
    assert [(o["label"], o["position"]) for o in options] == [("Apple", 1), ("Pear", 2), ("Plum", 3)]
    result = service.get_poll_result(poll_id)
    assert result["total"] == 0
    assert [o["votes"] for o in result["options"]] == [0, 0, 0]


@pytest.mark.parametrize(
    "question, options, message",
    [
        ("   ", ["A", "B"], "Please enter a question."),
        ("x" * 201, ["A", "B"], "The question must be 200 characters or fewer."),
        ("Q?", ["A", "  "], "Please enter at least two options."),
        ("Q?", ["A", "y" * 101], "Each option must be 100 characters or fewer."),
        ("Q?", ["A", " A "], "Each option must be different."),
    ],
)
def test_create_poll_rejects_invalid_input_without_recording(setup_data, question, options, message) -> None:
    conn, *_ = setup_data
    before = PollRepository(conn).count_polls()
    with pytest.raises(InvalidPoll) as err:
        VotingService(conn).create_poll(question, options, VOTED_AT)
    assert err.value.message == message
    assert PollRepository(conn).count_polls() == before
