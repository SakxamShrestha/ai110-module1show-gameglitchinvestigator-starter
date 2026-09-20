"""Pure game logic for the Glitchy Guesser.

Every function here is free of Streamlit calls so that the rules of the game
can be exercised by pytest without launching a web server. ``app.py`` is
responsible for presentation and session state only.

FIX: this module was built by moving the four functions out of app.py and
repairing them one at a time with my AI assistant. The AI proposed the module
layout and the docstrings. The decision to have check_guess return a bare
outcome string rather than a tuple was mine, because
tests/test_game_logic.py already asserts `check_guess(50, 50) == "Win"` and I
did not want to edit the starter tests to make my own code pass.
"""

DIFFICULTY_RANGES = {
    "Easy": (1, 20),
    "Normal": (1, 100),
    "Hard": (1, 200),
}

ATTEMPT_LIMITS = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}

# FIX (Bug 1): one table maps an outcome to its sentence. The starter typed the
# label and the message out together in six separate places, which is how
# "Too High" ended up paired with "Go HIGHER!". With a single lookup they
# cannot drift apart again.
HINTS = {
    "Win": "\U0001F389 Correct!",
    "Too High": "\U0001F4C9 Too high - guess LOWER.",
    "Too Low": "\U0001F4C8 Too low - guess HIGHER.",
}

DEFAULT_DIFFICULTY = "Normal"


def get_range_for_difficulty(difficulty):
    """Return the inclusive ``(low, high)`` guess range for a difficulty."""
    return DIFFICULTY_RANGES.get(difficulty, DIFFICULTY_RANGES[DEFAULT_DIFFICULTY])


def get_attempt_limit(difficulty):
    """Return how many guesses a player is allowed at a difficulty."""
    return ATTEMPT_LIMITS.get(difficulty, ATTEMPT_LIMITS[DEFAULT_DIFFICULTY])


def parse_guess(raw, low=None, high=None):
    """Convert raw text input into a validated integer guess.

    Returns an ``(ok, guess_int, error_message)`` triple so the caller can tell
    a rejected guess from an accepted one without catching an exception.
    """
    if raw is None:
        return False, None, "Enter a guess."

    text = str(raw).strip()
    if not text:
        return False, None, "Enter a guess."

    try:
        value = int(text)
    except ValueError:
        return False, None, f"'{text}' is not a whole number. Try something like 42."

    if low is not None and high is not None and not low <= value <= high:
        return False, None, f"Guess must be between {low} and {high}."

    return True, value, None


def check_guess(guess, secret):
    """Compare a guess against the secret and return the outcome label.

    Returns one of ``"Win"``, ``"Too High"`` or ``"Too Low"``.
    """
    # FIX (root cause behind Bug 4): both operands are coerced to int before
    # any comparison happens. The starter wrapped the comparison in
    # `try/except TypeError`, so when app.py handed it a stringified secret the
    # except block quietly retried as a string compare, where "9" > "50" is
    # True. Deleting that except block is the real fix. A bad value now fails
    # loudly instead of producing a confident wrong answer.
    guess = int(guess)
    secret = int(secret)

    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def hint_for(outcome):
    """Return the player-facing hint text for an outcome label."""
    return HINTS.get(outcome, "")


def update_score(current_score, outcome, attempt_number):
    """Return the new score after a guess.

    A win pays 100 points minus 10 for every attempt already used, never less
    than 10. Any wrong guess costs a flat 5 points, and the score is floored
    at zero.
    """
    if outcome == "Win":
        # FIX (Bug 4): the starter used `100 - 10 * (attempt_number + 1)`, so
        # winning on the very first guess paid 80 instead of 100.
        points = max(10, 100 - 10 * (attempt_number - 1))
        return current_score + points

    # FIX (Bug 4): every wrong outcome now costs the same 5 points. The starter
    # returned `current_score + 5` for a "Too High" on even-numbered attempts,
    # which is why a wrong guess could raise my score, and it had no floor, so
    # the total could go negative.
    if outcome in ("Too High", "Too Low"):
        return max(0, current_score - 5)

    return current_score


def proximity_label(guess, secret, low, high):
    """Return a hot/cold band describing how close a wrong guess was.

    The band is based on distance as a fraction of the playable range, so it
    stays meaningful at every difficulty level.
    """
    span = max(1, int(high) - int(low))
    ratio = abs(int(guess) - int(secret)) / span

    if ratio <= 0.05:
        return "\U0001F525 Burning hot"
    if ratio <= 0.15:
        return "\U00002668\U0000FE0F Hot"
    if ratio <= 0.30:
        return "\U0001F324\U0000FE0F Warm"
    if ratio <= 0.50:
        return "\U0001F9CA Cold"
    return "\U00002744\U0000FE0F Freezing"
