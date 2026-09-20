"""Streamlit front end for the Glitchy Guesser.

This module is deliberately thin: it owns page layout and Streamlit session
state, while every rule of the game lives in ``logic_utils`` so the rules can
be unit-tested without a browser.

FIX: the four game functions that used to be defined here were moved into
logic_utils.py. I asked my AI assistant to do the move and update the imports
in one instruction, then reviewed the diff function by function before
accepting it.
"""

import random

import streamlit as st

from logic_utils import (
    check_guess,
    get_attempt_limit,
    get_range_for_difficulty,
    hint_for,
    parse_guess,
    proximity_label,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="\U0001F3AE")


def start_new_game(difficulty):
    """Reset every per-round key in session state at once.

    FIX (Bug 3): the starter's New Game button reset only ``attempts`` and
    ``secret``. ``score``, ``status`` and ``history`` survived, so the very
    next rerun saw ``status == "won"``, hit ``st.stop()`` and hid the guess
    box - the board stayed locked and the old score carried over. It also drew
    the secret from a hard-coded 1-100 range, so on Easy the number was
    usually outside the stated range and unreachable. Routing every reset
    through one function is what makes a partial reset impossible: there is
    now exactly one writer of per-round state.
    """
    low, high = get_range_for_difficulty(difficulty)
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.active_difficulty = difficulty


st.title("\U0001F3AE Game Glitch Investigator")
st.caption("A number-guessing game, repaired.")

st.sidebar.header("Settings")
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)

low, high = get_range_for_difficulty(difficulty)
attempt_limit = get_attempt_limit(difficulty)

# The high score deliberately lives outside start_new_game so that it survives
# a New Game and persists for the whole browser session.
if "high_score" not in st.session_state:
    st.session_state.high_score = 0

# FIX (Bug 3): changing difficulty mid-game used to leave behind a secret that
# was outside the new range, making the round unwinnable. Re-deal instead.
if "secret" not in st.session_state or st.session_state.get("active_difficulty") != difficulty:
    start_new_game(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")
st.sidebar.metric("High score", st.session_state.high_score)


def render_history_sidebar():
    """Draw the running session table in the sidebar.

    Called from every exit path so the table always includes the guess that
    was just made, rather than lagging one rerun behind.
    """
    st.sidebar.subheader("Guess history")
    if st.session_state.history:
        st.sidebar.table(st.session_state.history)
    else:
        st.sidebar.caption("No guesses yet.")


# The banner position is reserved here but filled at the bottom of the script.
# Streamlit runs top to bottom, so writing the attempts count here would show
# the value from *before* the guess that is about to be processed.
status_slot = st.empty()


def render_status_banner():
    """Fill the reserved banner with the current range and attempts left.

    FIX (Bug 2): attempts now start at 0 on both a cold start and a New Game.
    The starter initialised them to 1 at line 96 but reset them to 0 at line
    135, which is why the banner read "Attempts left: 7" before I had played a
    single turn. The range is read live instead of being hard-coded to 1-100.
    """
    attempts_left = max(0, attempt_limit - st.session_state.attempts)
    status_slot.info(
        f"Guess a number between {low} and {high}. Attempts left: {attempts_left}"
    )


with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input("Enter your guess:", key=f"guess_input_{difficulty}")

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess \U0001F680")
with col2:
    new_game = st.button("New Game \U0001F501")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    start_new_game(difficulty)
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    render_status_banner()
    render_history_sidebar()
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess, low=low, high=high)

    # FIX (Bug 2): the starter ran `st.session_state.attempts += 1` at line 148
    # before parse_guess had validated anything, so typing "!!!" still cost a
    # turn. The counter is only touched on the accepted branch below now.
    if not ok:
        st.error(err)
    else:
        st.session_state.attempts += 1

        # FIX (Bug 1 / Bug 4): the secret is passed through untouched. The
        # starter cast it to str on every even attempt, which forced
        # check_guess into a string comparison and returned the wrong outcome
        # label - which then fed the scoring function bad input.
        outcome = check_guess(guess_int, st.session_state.secret)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        closeness = "-" if outcome == "Win" else proximity_label(
            guess_int, st.session_state.secret, low, high
        )
        st.session_state.history.append(
            {
                "#": st.session_state.attempts,
                "Guess": guess_int,
                "Result": outcome,
                "Closeness": closeness,
                "Score": st.session_state.score,
            }
        )

        if show_hint and outcome != "Win":
            # FIX (Bug 1): hint_for maps "Too High" to "guess LOWER", which is
            # the pairing the starter had backwards.
            st.warning(f"{hint_for(outcome)}  ({closeness})")

        if outcome == "Win":
            st.session_state.status = "won"
            st.session_state.high_score = max(
                st.session_state.high_score, st.session_state.score
            )
            st.balloons()
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.error(
                f"Out of attempts! The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}"
            )

render_status_banner()
render_history_sidebar()

st.divider()
st.caption("Repaired by a human who read the diff.")
