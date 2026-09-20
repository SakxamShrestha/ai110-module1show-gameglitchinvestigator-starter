"""Tests for the Glitchy Guesser.

Each section below is tagged with the bug number from reflection.md that it
guards against, so a future regression points straight back at the original
bug report.

The pure-logic tests import from logic_utils. Bugs 2 and 3 live in Streamlit
session state rather than in any function, so those are driven through
streamlit.testing.v1.AppTest, which runs the real app.py without a browser.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from logic_utils import (
    check_guess,
    get_attempt_limit,
    get_range_for_difficulty,
    hint_for,
    parse_guess,
    proximity_label,
    update_score,
)

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


def run_app():
    """Start a fresh run of app.py and return the AppTest handle."""
    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.run()
    return app


def submit_guess(app, text):
    """Type a guess and click Submit. Returns the app after the rerun."""
    app.text_input[0].set_value(str(text))
    app.button[0].click()
    app.run()
    return app


# ---------------------------------------------------------------------------
# Original starter tests, kept byte-for-byte. If these pass unedited, the
# refactor into logic_utils.py did not change the public contract.
# ---------------------------------------------------------------------------

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"


def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"


def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


# ---------------------------------------------------------------------------
# Bug 1: the hints pointed the wrong way
# ---------------------------------------------------------------------------

def test_bug1_guess_above_secret_is_told_to_go_lower():
    """Reproduction case: secret 25, guess 26, the game said "Go HIGHER!"."""
    outcome = check_guess(26, 25)

    assert outcome == "Too High"
    assert "LOWER" in hint_for(outcome)
    assert "HIGHER" not in hint_for(outcome)


def test_bug1_guess_below_secret_is_told_to_go_higher():
    """Reproduction case: secret 25, guess 24, the game said "Go LOWER!"."""
    outcome = check_guess(24, 25)

    assert outcome == "Too Low"
    assert "HIGHER" in hint_for(outcome)
    assert "LOWER" not in hint_for(outcome)


@pytest.mark.parametrize(
    "guess, expected",
    [(1, "Too Low"), (49, "Too Low"), (50, "Win"), (51, "Too High"), (100, "Too High")],
)
def test_bug1_hints_stay_consistent_across_the_whole_range(guess, expected):
    """Following the hint must always move the player toward the secret."""
    assert check_guess(guess, 50) == expected


def test_bug1_a_string_secret_does_not_compare_alphabetically():
    """The starter compared "9" > "50" as text, which is True. Compared as
    numbers it is False, and the number is what matters."""
    assert check_guess(9, "50") == "Too Low"
    assert check_guess(60, "50") == "Too High"
    assert check_guess("50", 50) == "Win"


# ---------------------------------------------------------------------------
# Bug 2: the attempt counter started at 1, and invalid input still cost a turn
# ---------------------------------------------------------------------------

def test_bug2_a_fresh_game_has_not_used_any_attempts():
    """Reproduction case: the banner read "Attempts left: 7" before playing."""
    app = run_app()

    assert app.session_state.attempts == 0
    assert "Attempts left: 8" in app.info[0].value


def test_bug2_invalid_input_does_not_cost_an_attempt():
    """Reproduction case: typing "!!!" dropped attempts left from 4 to 3."""
    app = run_app()
    submit_guess(app, "!!!")

    assert app.session_state.attempts == 0
    assert app.session_state.history == []
    assert "not a whole number" in app.error[0].value
    assert "Attempts left: 8" in app.info[0].value


def test_bug2_a_valid_guess_costs_exactly_one_attempt():
    app = run_app()
    wrong = app.session_state.secret % 100 + 1  # any number that is not the secret

    submit_guess(app, wrong)

    assert app.session_state.attempts == 1
    assert "Attempts left: 7" in app.info[0].value


# ---------------------------------------------------------------------------
# Bug 3: New Game did not start a new game
# ---------------------------------------------------------------------------

def test_bug3_new_game_after_a_win_resets_every_piece_of_state():
    """Reproduction case: after winning, the app stayed on "You already won"."""
    app = run_app()
    submit_guess(app, app.session_state.secret)

    assert app.session_state.status == "won"
    assert app.session_state.score > 0

    app.button[1].click()
    app.run()

    assert app.session_state.status == "playing"
    assert app.session_state.score == 0
    assert app.session_state.attempts == 0
    assert app.session_state.history == []


def test_bug3_new_game_brings_back_the_guess_box():
    """The guess box and Submit button vanished after a win."""
    app = run_app()
    submit_guess(app, app.session_state.secret)

    app.button[1].click()
    app.run()

    assert len(app.text_input) == 1
    assert app.button[0].label == "Submit Guess \U0001F680"

    # And the fresh round is genuinely playable.
    submit_guess(app, app.session_state.secret)
    assert app.session_state.status == "won"


def test_bug3_new_game_respects_the_difficulty_range():
    """New Game used a hard-coded randint(1, 100) regardless of difficulty."""
    app = run_app()
    app.selectbox[0].set_value("Easy")
    app.run()

    for _ in range(20):
        app.button[1].click()
        app.run()
        assert 1 <= app.session_state.secret <= 20


def test_bug3_the_high_score_survives_a_new_game():
    """The high score is the one value that is meant to persist."""
    app = run_app()
    submit_guess(app, app.session_state.secret)
    won_with = app.session_state.score

    app.button[1].click()
    app.run()

    assert app.session_state.score == 0
    assert app.session_state.high_score == won_with


# ---------------------------------------------------------------------------
# Bug 4: the score moved the wrong way and could go negative
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("attempt_number", [1, 2, 3, 4, 5, 6, 7, 8])
def test_bug4_a_wrong_guess_never_pays_points(attempt_number):
    """The starter paid +5 for "Too High" on even-numbered attempts."""
    assert update_score(50, "Too High", attempt_number) == 45
    assert update_score(50, "Too Low", attempt_number) == 45


def test_bug4_the_score_does_not_bounce_across_four_wrong_guesses():
    """Reproduction case: the score bounced 5, 0, 5, 0 instead of settling."""
    score = 40
    history = []

    for attempt_number in range(1, 5):
        score = update_score(score, "Too High", attempt_number)
        history.append(score)

    assert history == [35, 30, 25, 20]


def test_bug4_the_score_never_goes_negative():
    score = 0

    for attempt_number in range(1, 6):
        score = update_score(score, "Too Low", attempt_number)
        assert score >= 0


def test_bug4_winning_on_the_first_attempt_pays_full_marks():
    """The starter's formula used (attempt_number + 1) and paid 80 here."""
    assert update_score(0, "Win", 1) == 100
    assert update_score(0, "Win", 2) == 90


def test_bug4_the_win_payout_shrinks_with_each_attempt_used():
    payouts = [update_score(0, "Win", n) for n in range(1, 9)]

    assert payouts == [100, 90, 80, 70, 60, 50, 40, 30]
    assert payouts == sorted(payouts, reverse=True)


def test_bug4_the_win_payout_floors_at_ten():
    assert update_score(0, "Win", 12) == 10
    assert update_score(0, "Win", 50) == 10


def test_bug4_an_unknown_outcome_leaves_the_score_alone():
    assert update_score(37, "Something Else", 3) == 37


def test_bug4_the_score_only_rises_on_a_win_during_real_play():
    app = run_app()
    secret = app.session_state.secret
    wrong = secret % 100 + 1

    submit_guess(app, wrong)
    assert app.session_state.score == 0  # floored, never paid for a miss

    submit_guess(app, secret)
    assert app.session_state.score == 90  # won on attempt 2
    assert app.session_state.status == "won"


# ---------------------------------------------------------------------------
# Edge cases for parse_guess
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["abc", "!!!", "ten", "5 0", "1e3", "50.5"])
def test_parse_guess_rejects_non_numeric_input(raw):
    ok, value, error = parse_guess(raw)

    assert ok is False
    assert value is None
    assert error


@pytest.mark.parametrize("raw", ["", "   ", "\t", None])
def test_parse_guess_rejects_empty_input(raw):
    ok, value, error = parse_guess(raw)

    assert ok is False
    assert error == "Enter a guess."


def test_parse_guess_rejects_negative_numbers_outside_the_range():
    ok, _, error = parse_guess("-5", low=1, high=100)

    assert ok is False
    assert "between 1 and 100" in error


def test_parse_guess_rejects_numbers_above_the_range():
    ok, _, error = parse_guess("101", low=1, high=100)

    assert ok is False
    assert "between 1 and 100" in error


def test_parse_guess_range_bounds_are_inclusive():
    assert parse_guess("1", low=1, high=100)[0] is True
    assert parse_guess("100", low=1, high=100)[0] is True


def test_parse_guess_strips_surrounding_whitespace():
    assert parse_guess("  42  ", low=1, high=100) == (True, 42, None)


# ---------------------------------------------------------------------------
# Difficulty settings
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "difficulty, expected",
    [("Easy", (1, 20)), ("Normal", (1, 100)), ("Hard", (1, 200)), ("Unknown", (1, 100))],
)
def test_get_range_for_difficulty(difficulty, expected):
    assert get_range_for_difficulty(difficulty) == expected


def test_hard_is_actually_harder_than_normal():
    """The starter gave Hard the range 1-50, narrower than Normal's 1-100."""
    _, normal_high = get_range_for_difficulty("Normal")
    _, hard_high = get_range_for_difficulty("Hard")

    assert hard_high > normal_high
    assert get_attempt_limit("Hard") < get_attempt_limit("Normal")


def test_proximity_label_gets_colder_with_distance():
    assert "Burning hot" in proximity_label(51, 50, 1, 100)
    assert "Freezing" in proximity_label(99, 1, 1, 100)
