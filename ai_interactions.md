# AI Interactions Log

This file documents the stretch features I attempted. My AI coding assistant
throughout was **Claude Code (Claude Opus 5)** running in VS Code, with
`app.py`, `logic_utils.py` and `tests/test_game_logic.py` in its context so it
could see how my UI file and my logic file related to each other.

---

## Agent Workflow (SF8)

### What task did you give the agent?

Once the four bugs from `reflection.md` were fixed, I asked the agent to add
three features in one multi-step instruction:

> Add three features to the guessing game without changing the rules I already
> fixed in logic_utils.py: a high-score tracker that survives New Game, a
> guess-history table in the sidebar, and difficulty levels that actually
> change both the range and the attempt limit. Keep all existing tests passing.

### What did the agent do?

| File | What changed |
|------|--------------|
| `logic_utils.py` | Added `DIFFICULTY_RANGES` and `ATTEMPT_LIMITS` tables, `get_attempt_limit()`, and `proximity_label()` for the hot/cold bands |
| `app.py` | Added `start_new_game()`, `render_history_sidebar()`, `render_status_banner()`, a `high_score` session key, and an `active_difficulty` guard that re-deals the secret when the difficulty changes |
| `tests/test_game_logic.py` | Added `test_bug3_the_high_score_survives_a_new_game`, `test_bug3_new_game_respects_the_difficulty_range`, `test_hard_is_actually_harder_than_normal` and `test_proximity_label_gets_colder_with_distance` |

Commands it ran to check its own work: `pytest`, `flake8 --max-line-length=100`,
and `python play_session.py`.

### What did you have to verify or fix manually?

Four things, in the order I hit them.

**1. It rewrote three files at once and went past what I asked.** The first
attempt replaced `logic_utils.py`, `app.py` and the whole test file in a single
pass. The result genuinely worked — 42 tests passed — but it had gone further
than my instruction and I could not account for every change in it. Because my
last commit was a clean checkpoint, I rolled the working tree back with
`git stash` and started again more slowly. I kept it in the stash rather than
deleting it so I could still read what it had done.

**2. It added a feature I never asked for.** A later `logic_utils.py` arrived
carrying a `proximity_label()` function and a change to the `Hard` range from
`(1, 50)` to `(1, 200)`. I stopped and asked it to justify the file before I
pasted anything. Neither change mapped to a bug I had logged. The Hard range
genuinely is a bug — the starter made Hard *narrower* than Normal, so Hard was
the easiest setting — but it was not one I had documented or reproduced. I
decided to keep both, but as a deliberate stretch feature described in the
README, not smuggled in as a bug fix.

**3. A trailing `st.rerun()` erased the win message.** Its submit handler ended
with `st.rerun()` so the sidebar history would refresh. But a rerun restarts
the script from the top, `status` is already `"won"`, and the script then hits
the "You already won" branch — so the balloons and the "You won! The secret
was 50" line were wiped before a player could read them. I removed the
`st.rerun()`.

**4. The sidebar history lagged one guess behind.** With the rerun gone, the
sidebar was drawn before the submit handler had appended the new guess, so it
always showed the previous state. I moved the rendering into
`render_history_sidebar()` and called it from every exit path, including the
one guarded by `st.stop()`. The same problem applied to the attempts banner,
which I solved with `st.empty()` to reserve the position and fill it at the end
of the script.

---

## Test Generation (SF7)

**Prompt used:**

> Write pytest cases for `parse_guess` covering non-numeric strings, empty and
> whitespace-only input, `None`, negative numbers, and values just outside the
> allowed range. Use `@pytest.mark.parametrize` where the cases are similar.

| Edge Case | Why I chose it | AI-Suggested Test | Did It Pass? |
|-----------|----------------|-------------------|--------------|
| `"abc"`, `"!!!"`, `"ten"` | Text typed into a numeric field is the most common real user mistake, and `"!!!"` is the exact input from my Bug 2 reproduction row | `test_parse_guess_rejects_non_numeric_input` | Yes |
| `""`, `"   "`, `"\t"`, `None` | Streamlit sends an empty string on the very first page load, so this branch runs before the player has typed anything | `test_parse_guess_rejects_empty_input` | Yes |
| `"-5"` | A negative number is a *valid* integer, so it slips straight past `int()` and needs a separate range check to catch | `test_parse_guess_rejects_negative_numbers_outside_the_range` | Yes |
| `"101"` | Above the range is the mirror case, and out-of-range guesses would otherwise waste attempts on impossible numbers | `test_parse_guess_rejects_numbers_above_the_range` | Yes |
| `"1"` and `"100"` | Off-by-one at the boundary is exactly the bug class I had just fixed in the attempt counter, so I wanted the range check pinned as inclusive | `test_parse_guess_range_bounds_are_inclusive` | Yes |
| `"50.5"`, `"1e3"` | The starter silently truncated decimals with `int(float(raw))`, so a guess of 50.9 became 50 and the hint described a number the player had not entered | part of the non-numeric parametrize | Yes |
| `"  42  "` | Copy-pasted input almost always carries whitespace, and the starter never stripped it | `test_parse_guess_strips_surrounding_whitespace` | Yes |

### One case the AI suggested that I removed

It proposed asserting that `parse_guess("٤٢")` is rejected as non-numeric. I
added it and ran `pytest`, and the test **failed**:

```
FAILED tests/test_game_logic.py::test_parse_guess_rejects_non_numeric_strings[٤٢]
    assert ok is False
E   assert True is False
```

Python's `int()` accepts Unicode decimal digits, so `int("٤٢")` returns `42`
and the guess is parsed successfully. The AI had asserted behaviour it assumed
rather than behaviour it had checked. I removed the case instead of writing a
special rule to reject it — accepting Arabic-Indic numerals is reasonable
behaviour, and the test was wrong, not the code.

This is the clearest example I found of why running the test matters more than
reading it. The assertion looked completely plausible.

---

## Linting & Style (SF9)

**Prompt used:**

> Add professional docstrings to every function in `logic_utils.py`, give both
> modules a module-level docstring, and make the whole project pass
> `flake8 --max-line-length=100`.

**Linting output before** — the original starter, recovered from git commit
`ba85c5b`:

```
$ flake8 --max-line-length=100 app.py logic_utils.py
app.py:4:1: E302 expected 2 blank lines, found 1
app.py:67:1: E305 expected 2 blank lines after class or function definition, found 1
```

**Linting output after:**

```
$ flake8 --max-line-length=100 app.py logic_utils.py tests/ play_session.py
(no output)
exit code: 0
```

Both runs are committed in [`lint_report.txt`](lint_report.txt).

**Changes applied:**

- Two blank lines around every top-level definition, fixing `E302` and `E305`
- Module-level docstrings on `app.py`, `logic_utils.py`, `play_session.py` and
  `tests/test_game_logic.py`
- A docstring on all seven functions in `logic_utils.py`, each stating what the
  function returns rather than restating its name
- The multi-name import from `logic_utils` wrapped in parentheses, one name per
  line and alphabetised
- `# FIX (Bug n):` comments next to each repair, naming the bug from
  `reflection.md` that the line addresses

**A style suggestion I did not apply.** The AI wanted to rename `check_guess`
to `evaluate_guess_against_secret`. The longer name is more descriptive and I
agree it reads better in isolation. But `tests/test_game_logic.py` imports
`check_guess` by name, and the assignment asks me to keep the starter tests
working. Renaming it would have meant editing the starter tests to match my
code, which is backwards — the tests are the contract. Clarity that breaks a
contract is not an improvement.

---

## Model Comparison (SF11)

**Task given to both models:**

> Here is a Python function from a Streamlit game. A guess of 9 against a
> secret of 50 reports "Too High". Explain why, and give me a corrected
> version.

followed by the starter's `check_guess` (`app.py` lines 32–47) and the caller
that stringifies the secret (`app.py` lines 158–161):

```python
def check_guess(guess, secret):
    if guess == secret:
        return "Win", "🎉 Correct!"

    try:
        if guess > secret:
            return "Too High", "📈 Go HIGHER!"
        else:
            return "Too Low", "📉 Go LOWER!"
    except TypeError:
        g = str(guess)
        if g == secret:
            return "Win", "🎉 Correct!"
        if g > secret:
            return "Too High", "📈 Go HIGHER!"
        return "Too Low", "📉 Go LOWER!"


# ... and the caller, at app.py lines 158-161:
if st.session_state.attempts % 2 == 0:
    secret = str(st.session_state.secret)
else:
    secret = st.session_state.secret
```

| | Model A | Model B |
|-|---------|---------|
| **Model name** | Claude Opus 5 (via Claude Code) | Google Gemini |
| **Response summary** | Traced the full chain in order: `9 == "50"` returns `False` without error because Python compares int to str with `==` quite happily; `9 > "50"` then raises `TypeError` because ordering across those types is not defined; the `except TypeError` block catches it and retries as `str(9) > "50"`; `"9" > "50"` is `True` because string comparison goes character by character and `"9"` sorts after `"5"` regardless of length. Identified the **`except TypeError` block** as the root cause rather than the `str()` cast, on the grounds that the cast creates a loud error and the `except` is what converts it into a silent wrong answer. Fix: delete the `except` entirely, coerce both operands with `int()`, and return a bare outcome string with the hint text moved to a separate lookup. | Named the problem immediately as lexicographic comparison and explained it with ASCII values: `'9'` is 57, `'5'` is 53, so `"9" > "50"` is `True`. Spotted, without being asked, that the hint text is inverted as a **separate secondary bug** - `"Too High"` was paired with `"Go HIGHER!"`. Also pointed out a case I had not considered: if the guess arrives from Streamlit as a string, the comparison never raises at all and goes straight down the lexicographic path inside the `try`. Fix: cast both values with `int()` up front, wrap that in `except (ValueError, TypeError)` returning a new `"Invalid"` outcome, swap the two hint sentences, and remove the alternating `str()` cast from the caller. |
| **More Pythonic?** | Yes, for this codebase. Returns a bare outcome string, which is what the existing `tests/test_game_logic.py` asserts, and pushes the hint text into a `HINTS` dict so the label and the sentence cannot drift apart. No exception handling around the comparison at all. | Cleaner to read in isolation - the `if/elif/else` chain is tidier than what I ended up with. But it returns **tuples**, and it re-introduces an `except` around the `int()` cast that returns a fourth outcome, `"Invalid"`, which nothing downstream handles. |
| **Clearer explanation?** | Went deeper. It was the only one to notice that `9 == "50"` returns `False` silently, which means a genuinely **winning** guess also fails on an even-numbered attempt. It also argued *which line* is to blame and why. Longer, and took more reading. | Easier to follow on a first read. Three labelled points, the ASCII numbers stated outright, and a short corrected snippet. If I had been handed only this, I would have understood the bug faster. |

**Which did you prefer and why?**

They split it, and I did not expect that going in.

**Gemini gave the clearer explanation.** It led with the actual answer -
lexicographic comparison - and backed it with the ASCII numbers, `'9'` is 57
and `'5'` is 53. Three labelled points and it was done. Claude's walkthrough
was more thorough but I had to read it twice. Gemini also caught something on
its own initiative that I had been treating as a separate bug entirely: it
flagged the inverted hint text as a secondary defect without being asked about
it. And it raised a case neither I nor Claude had considered - if the guess
arrives from Streamlit as a *string*, the comparison never raises `TypeError`
at all and goes straight down the lexicographic path inside the `try`, so the
`except` is not even required to trigger the bug.

**Claude gave the fix that actually fits this codebase**, and I only found that
out by testing Gemini's version rather than reading it. Gemini's
`check_guess` returns tuples, so I ran it against my three starter tests:

```
test_winning_guess : result=('Win', '🎉 Correct!')  == 'Win' ?  False
test_guess_too_high: result=('Too High', '📉 Go LOWER!')  == 'Too High' ?  False
test_guess_too_low : result=('Too Low', '📈 Go HIGHER!')  == 'Too Low' ?  False
```

All three fail. They assert `check_guess(50, 50) == "Win"`, and a tuple is
never equal to a string. Adopting Gemini's version would have meant editing
the starter tests so my code could pass them, which is backwards.

The deeper problem is its `except (ValueError, TypeError)` around the `int()`
cast, returning a new `"Invalid"` outcome. That is the same shape as the bug we
were fixing - an `except` that swallows a type error and returns a plausible
value instead. Nothing downstream knows what `"Invalid"` means:
`update_score` has no branch for it and falls through unchanged, and `app.py`'s
`if outcome == "Win": ... else:` treats it as an ordinary wrong guess, so the
player loses an attempt to a typo. Validation already lives in `parse_guess`,
which is the right place for it. Gemini fixed the bug and quietly planted a
smaller one of the same species.

**What I took from the comparison:** the more readable explanation and the
better-fitting fix did not come from the same model, so "which is better" was
the wrong question. Gemini is what I would hand someone who needs to understand
this bug in two minutes. Claude's is what I would merge. And the only reason I
can tell them apart with any confidence is that I ran Gemini's code against my
tests instead of judging it by how it read.
