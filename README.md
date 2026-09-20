# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

An AI was asked to build a simple "Number Guessing Game" in Streamlit. It wrote
the code, declared it production-ready, and left behind a game that could not
be won. The hints pointed the wrong way, the attempt counter lied, the New Game
button did nothing, and the score went up when you guessed wrong.

This repo is the record of finding those bugs, reproducing them, repairing
them, and locking the repairs behind tests.

## 🎯 What the Game Does

The player guesses a hidden number inside a range set by the difficulty level.
After each guess the game says whether the guess was too high or too low and
how close it was, and it deducts points for a miss. Guessing correctly ends the
round and pays out points based on how few attempts it took. A high score
persists across rounds for the whole session.

| Difficulty | Range | Attempts |
|------------|-------|----------|
| Easy | 1 – 20 | 6 |
| Normal | 1 – 100 | 8 |
| Hard | 1 – 200 | 5 |

## 🛠️ Setup

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Run the tests with:

```bash
pytest
```

If you see `ImportError: numpy.core.multiarray failed to import` on launch,
your environment has a `pyarrow` built against NumPy 1.x while NumPy 2.x is
installed. Fix it with:

```bash
pip install --upgrade "pyarrow>=17" numexpr bottleneck
```

## 📝 Document Your Experience

- [x] **Describe the game's purpose.** See "What the Game Does" above.
- [x] **Detail which bugs you found.** See "Bugs Found" below, and the full
      reproduction table in [`reflection.md`](reflection.md).
- [x] **Explain what fixes you applied.** See "Fixes Applied" below.

## 🐛 Bugs Found

All four were found by playing the game and confirmed against the unmodified
starter code. Full reproduction steps, with expected vs actual behaviour for
each, are in [`reflection.md`](reflection.md).

| # | Where | What went wrong |
|---|-------|-----------------|
| 1 | `app.py:37-40` | **The hints pointed the wrong way.** With the secret at 25, guessing 26 returned `📈 Go HIGHER!` and guessing 24 returned `📉 Go LOWER!`. Following the game's own advice moved you further from the answer. |
| 2 | `app.py:96`, `:135`, `:148` | **The attempt counter was wrong and typos cost a turn.** The sidebar promised 8 attempts but the banner read "Attempts left: 7" before a single guess, because `attempts` initialised to 1 on a cold start and 0 after New Game. `attempts += 1` also ran *before* input was validated, so typing `!!!` consumed a turn. |
| 3 | `app.py:134-138` | **New Game did not start a new game.** It reset only `attempts` and `secret`; `score`, `status` and `history` survived, so the next rerun saw `status == "won"`, hit `st.stop()`, and hid the guess box. It also drew the secret from a hard-coded 1–100 range regardless of difficulty. |
| 4 | `app.py:52`, `:57-60` | **The score moved the wrong way.** `update_score` returned `current_score + 5` for a wrong "Too High" on even-numbered attempts, so a miss could *raise* your score. There was no floor, so it could also go negative. A first-guess win paid 80 instead of 100 because the payout used `(attempt_number + 1)`. |

A fifth defect sat underneath bugs 1 and 4: `app.py:158-161` cast the secret to
a string on every even attempt. Comparing `int` to `str` raised `TypeError`,
and a `try/except TypeError` block in `check_guess` swallowed the error and
silently retried as a *string* comparison, where `"9" > "50"` is `True`. That
is why every row of the reproduction table has `none` in the console output
column — the program never crashed, it just returned confident wrong answers.

## 🔧 Fixes Applied

Every game rule moved out of `app.py` into `logic_utils.py`, which imports no
Streamlit at all and can therefore be tested without a browser.

- **`check_guess`** coerces both operands with `int()` and returns a bare
  outcome string. The `try/except TypeError` that converted a type error into
  an alphabetical comparison was deleted rather than patched — a bad value now
  fails loudly instead of producing a plausible wrong answer.
- **`hint_for`** reads a single `HINTS` dictionary, so an outcome label and its
  sentence come from one place and cannot drift apart. The starter had typed
  them out together in six locations, which is how they got reversed.
- **`update_score`** applies a flat −5 to every wrong outcome with a floor at
  0, and pays `100 - 10 * (attempt_number - 1)` for a win, so a first-guess win
  pays the full 100.
- **`parse_guess`** strips whitespace, rejects non-integers with a readable
  message, and range-checks the guess against the active difficulty.
- **`start_new_game`** in `app.py` is now the *only* writer of per-round state.
  A reset cannot be partial because there is exactly one place that performs
  one, and it re-deals the secret inside the correct difficulty range.
- **Attempts increment after validation**, so rejected input is free.
- **The status banner** is drawn into a reserved `st.empty()` slot and filled
  at the end of the script. Streamlit runs top to bottom, so a banner written
  above the submit handler shows the count from *before* the guess.

## 📸 Demo Walkthrough

A full round on **Normal** difficulty, with the secret at 50. This is the real
behaviour of the repaired game — it can be reproduced by running
`python play_session.py`.

1. Launch with `python -m streamlit run app.py`. Difficulty defaults to
   **Normal**, the banner reads *"Guess a number between 1 and 100. Attempts
   left: 8"*, and the sidebar guess history is empty.
2. Enter `abc` and press Submit. The game shows *"'abc' is not a whole number.
   Try something like 42."* and **Attempts left stays at 8** — invalid input no
   longer costs a turn.
3. Enter `25`. The hint reads **📈 Too low - guess HIGHER** with a closeness
   band of *🌤️ Warm*. Attempts left drops to 7 and the guess is added to the
   sidebar history table.
4. Enter `75`. The hint reads **📉 Too high - guess LOWER** — the opposite
   direction from step 3, which is the pairing the starter had backwards.
   Attempts left drops to 6.
5. Enter `60`. Still too high, but the band tightens to *♨️ Hot* because the
   guess is now much closer to the secret. Attempts left drops to 5.
6. Enter `50`. Balloons, and *"You won! The secret was 50. Final score: 70"* —
   won on attempt 4, so the payout is `100 - 10 * 3`. The sidebar **High
   score** metric updates to 70.
7. Click **New Game 🔁**. Score returns to 0, attempts to 8, the history table
   clears, and the guess box comes back — but the High score metric keeps 70.
8. Switch difficulty to **Hard**. The range becomes 1–200, the attempt limit
   drops to 5, and a fresh secret is dealt inside the new range so the round
   stays winnable.

## 🧪 Test Results

53 tests, covering the three original starter tests (kept byte-for-byte
unedited), one or more regression tests per documented bug, and edge cases for
`parse_guess`.

Bugs 2 and 3 live in Streamlit session state rather than in any function, so
those are driven through `streamlit.testing.v1.AppTest`, which runs the real
`app.py` headless and asserts on `st.session_state` after a button click.

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-8.4.2, pluggy-1.6.0 -- /opt/anaconda3/bin/python
cachedir: .pytest_cache
rootdir: .
configfile: pytest.ini
testpaths: tests
plugins: mock-3.15.1, asyncio-1.2.0, Faker-40.13.0, anyio-4.2.0, hydra-core-1.3.2
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 53 items

tests/test_game_logic.py::test_winning_guess PASSED                      [  1%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [  3%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [  5%]
tests/test_game_logic.py::test_bug1_guess_above_secret_is_told_to_go_lower PASSED [  7%]
tests/test_game_logic.py::test_bug1_guess_below_secret_is_told_to_go_higher PASSED [  9%]
tests/test_game_logic.py::test_bug1_hints_stay_consistent_across_the_whole_range[1-Too Low] PASSED [ 11%]
tests/test_game_logic.py::test_bug1_hints_stay_consistent_across_the_whole_range[49-Too Low] PASSED [ 13%]
tests/test_game_logic.py::test_bug1_hints_stay_consistent_across_the_whole_range[50-Win] PASSED [ 15%]
tests/test_game_logic.py::test_bug1_hints_stay_consistent_across_the_whole_range[51-Too High] PASSED [ 16%]
tests/test_game_logic.py::test_bug1_hints_stay_consistent_across_the_whole_range[100-Too High] PASSED [ 18%]
tests/test_game_logic.py::test_bug1_a_string_secret_does_not_compare_alphabetically PASSED [ 20%]
tests/test_game_logic.py::test_bug2_a_fresh_game_has_not_used_any_attempts PASSED [ 22%]
tests/test_game_logic.py::test_bug2_invalid_input_does_not_cost_an_attempt PASSED [ 24%]
tests/test_game_logic.py::test_bug2_a_valid_guess_costs_exactly_one_attempt PASSED [ 26%]
tests/test_game_logic.py::test_bug3_new_game_after_a_win_resets_every_piece_of_state PASSED [ 28%]
tests/test_game_logic.py::test_bug3_new_game_brings_back_the_guess_box PASSED [ 30%]
tests/test_game_logic.py::test_bug3_new_game_respects_the_difficulty_range PASSED [ 32%]
tests/test_game_logic.py::test_bug3_the_high_score_survives_a_new_game PASSED [ 33%]
tests/test_game_logic.py::test_bug4_a_wrong_guess_never_pays_points[1] PASSED [ 35%]
tests/test_game_logic.py::test_bug4_a_wrong_guess_never_pays_points[2] PASSED [ 37%]
tests/test_game_logic.py::test_bug4_a_wrong_guess_never_pays_points[3] PASSED [ 39%]
tests/test_game_logic.py::test_bug4_a_wrong_guess_never_pays_points[4] PASSED [ 41%]
tests/test_game_logic.py::test_bug4_a_wrong_guess_never_pays_points[5] PASSED [ 43%]
tests/test_game_logic.py::test_bug4_a_wrong_guess_never_pays_points[6] PASSED [ 45%]
tests/test_game_logic.py::test_bug4_a_wrong_guess_never_pays_points[7] PASSED [ 47%]
tests/test_game_logic.py::test_bug4_a_wrong_guess_never_pays_points[8] PASSED [ 49%]
tests/test_game_logic.py::test_bug4_the_score_does_not_bounce_across_four_wrong_guesses PASSED [ 50%]
tests/test_game_logic.py::test_bug4_the_score_never_goes_negative PASSED [ 52%]
tests/test_game_logic.py::test_bug4_winning_on_the_first_attempt_pays_full_marks PASSED [ 54%]
tests/test_game_logic.py::test_bug4_the_win_payout_shrinks_with_each_attempt_used PASSED [ 56%]
tests/test_game_logic.py::test_bug4_the_win_payout_floors_at_ten PASSED  [ 58%]
tests/test_game_logic.py::test_bug4_an_unknown_outcome_leaves_the_score_alone PASSED [ 60%]
tests/test_game_logic.py::test_bug4_the_score_only_rises_on_a_win_during_real_play PASSED [ 62%]
tests/test_game_logic.py::test_parse_guess_rejects_non_numeric_input[abc] PASSED [ 64%]
tests/test_game_logic.py::test_parse_guess_rejects_non_numeric_input[!!!] PASSED [ 66%]
tests/test_game_logic.py::test_parse_guess_rejects_non_numeric_input[ten] PASSED [ 67%]
tests/test_game_logic.py::test_parse_guess_rejects_non_numeric_input[5 0] PASSED [ 69%]
tests/test_game_logic.py::test_parse_guess_rejects_non_numeric_input[1e3] PASSED [ 71%]
tests/test_game_logic.py::test_parse_guess_rejects_non_numeric_input[50.5] PASSED [ 73%]
tests/test_game_logic.py::test_parse_guess_rejects_empty_input[] PASSED  [ 75%]
tests/test_game_logic.py::test_parse_guess_rejects_empty_input[   ] PASSED [ 77%]
tests/test_game_logic.py::test_parse_guess_rejects_empty_input[\t] PASSED [ 79%]
tests/test_game_logic.py::test_parse_guess_rejects_empty_input[None] PASSED [ 81%]
tests/test_game_logic.py::test_parse_guess_rejects_negative_numbers_outside_the_range PASSED [ 83%]
tests/test_game_logic.py::test_parse_guess_rejects_numbers_above_the_range PASSED [ 84%]
tests/test_game_logic.py::test_parse_guess_range_bounds_are_inclusive PASSED [ 86%]
tests/test_game_logic.py::test_parse_guess_strips_surrounding_whitespace PASSED [ 88%]
tests/test_game_logic.py::test_get_range_for_difficulty[Easy-expected0] PASSED [ 90%]
tests/test_game_logic.py::test_get_range_for_difficulty[Normal-expected1] PASSED [ 92%]
tests/test_game_logic.py::test_get_range_for_difficulty[Hard-expected2] PASSED [ 94%]
tests/test_game_logic.py::test_get_range_for_difficulty[Unknown-expected3] PASSED [ 96%]
tests/test_game_logic.py::test_hard_is_actually_harder_than_normal PASSED [ 98%]
tests/test_game_logic.py::test_proximity_label_gets_colder_with_distance PASSED [100%]

============================== 53 passed in 1.15s ==============================
```

An end-to-end session replay, including the invalid-input and win paths, is in
[`play_session.py`](play_session.py). Run `python play_session.py` to reproduce
it. Linter output is in [`lint_report.txt`](lint_report.txt) — `flake8
--max-line-length=100` reports zero issues.

## 🚀 Stretch Features

**Enhanced UI and formatting.** `hint_for()` returns emoji-prefixed directional
hints (📈 / 📉), and `proximity_label()` grades every wrong guess into a
🔥 Burning hot → ♨️ Hot → 🌤️ Warm → 🧊 Cold → ❄️ Freezing band based on distance
as a fraction of the playable range, so it stays meaningful at every
difficulty. `render_history_sidebar()` draws a live session table of every
guess with its result, closeness band and running score, and a **High score**
metric persists across rounds.

**Difficulty levels.** `get_range_for_difficulty()` and `get_attempt_limit()`
drive Easy (1–20, 6 tries), Normal (1–100, 8 tries) and Hard (1–200, 5 tries).
The starter gave Hard the range 1–50, *narrower* than Normal, which made Hard
the easiest setting. Changing difficulty mid-session re-deals the secret rather
than leaving an unreachable one behind.

**Advanced edge-case testing.** `parse_guess` is tested against non-numeric
strings, symbols, embedded spaces, scientific notation, decimals, empty and
whitespace-only input, `None`, negative numbers, values above the range, and
both inclusive boundaries.

**Professional documentation and style.** Every function in `logic_utils.py`
carries a docstring, both modules have module-level docstrings, and the
codebase passes `flake8 --max-line-length=100` with zero warnings. Before and
after linter output is committed in [`lint_report.txt`](lint_report.txt).

The prompts used for each stretch feature, the rationale behind every edge
case, the agent workflow, and the corrections I had to make by hand are all
documented in [`ai_interactions.md`](ai_interactions.md). A terminal trace of
the original broken game is in
[`bug_trace_before.txt`](bug_trace_before.txt).
