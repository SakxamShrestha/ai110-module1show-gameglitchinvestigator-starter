# 💭 Reflection: Game Glitch Investigator

## 1. What was broken when you started?

Just launching the opening the game, there was no visible bug, but my each attempt against the secret gave me wrong direction. I played 4-5 rounds of game and could not win by myself (which we can if we do mental binary search usually), and by looking in the secret in the developer panel I figured out there is some problems in the backend logic. 

**Bug 1 — The hints point the wrong way.**
I set up a round where the secret was 25 and I guessed 26. The game told me "Go HIGHER!". I then guessed 24 instead and it told me "Go LOWER!". Both hints sent me away from the answer, so following the game's own advice took me further from the number every turn.

**Bug 2 — The attempt counter is wrong, and typos cost you a turn.**
The sidebar says "Attempts allowed: 8", but the moment the page loads and before I have guessed anything, the banner already reads "Attempts left: 7". I lost a turn just by opening the game. It gets worse if we mistype anything other than words. I typed some other symbols and characters for testing, and got "That is not a number", but the counter still dropped, from reamining 4 to 3. Invalid inputs still cost you. 

**Bug 3 — The New Game button doesn't start a new game.**
After I finally won a round by typing the secret, I clicked "New Game started." and then the page went straight back to "You already won. Start a new game to play again." The guess box and Submit button disappear, so there is no way to keep playing. My score from the previous round also carried over instead of resetting to 0. The only way to act to stop the server and restart it.

**Bug 4 — The score moves in the wrong direction, and can even go negative.**
I opened "Developer Debug Info" so I could watch the score while I played. With the secret at 25, I guessed 30 and the score went up from 0 to 5. The game paid me for missing. I guessed 20, also wrong, and it went back down to 0. Four wrong guesses in a row and the score just bounced 5, 0, 5, 0 without settling anywhere.

**Bug Reproduction Log**

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
| (Bug 1) Guess `26` when the secret is `25` | Hint tells me to go lower | Hint reads ` Go HIGHER!` | none |
| (Bug 1) Guess `24` when the secret is `25` | Hint tells me to go higher | Hint reads `Go LOWER!` | none |
| (Bug 2) Load the page, guess nothing | "Attempts left: 8", matching the sidebar's "Attempts allowed: 8" | "Attempts left: 7" before I have played a single turn | none |
| (Bug 2) Type `!!!` and press Submit | Error shown, attempt not counted | `That is not a number.` shown and attempts left dropped from 4 to 3 | none |
| (Bug 3) Click **New Game ** after winning a round | Fresh round: score 0, attempts reset, guess box returns | "You already won. Start a new game to play again." Guess box and Submit button gone; previous score kept | none |
| (Bug 4) Guess `30` as my first guess when the secret is `25` | Wrong guess, so the score should drop | Score rose from 0 to 5 | none |
| (Bug 4) Guess `20` next, still wrong | Score drops again | Score returned to 0, then bounced 5, 0, 5, 0 across four wrong guesses | none |

## 2. How did you use AI as a teammate?

I used Claude Code as my primary AI coding assistant, working in VS Code with `app.py`
and `logic_utils.py` in context so it could see how my UI file and my logic
file related to each other.

**An AI explanation that helped me.** Before I changed anything, I marked five
`# FIXME:` comments in `app.py` at the places I suspected where errors were. Then I asked about
the strangest one: "explain step by step what happens on attempt 2 when the
secret is 50 and I guess 9."

It walked me through the whole chain. On attempt 2, line 158 evaluates
`attempts % 2 == 0` as true, so line 159 runs `secret = str(50)` and the secret
becomes the string `"50"`. Inside `check_guess`, line 33 tests `9 == "50"` and
gets `False` - Python compares an int to a string without complaining, it just
answers False, which meant even a winning guess would have failed there. Line
37 then tests `9 > "50"` and raises `TypeError`, because Python will not order
an int against a string. Line 41 catches that error and retries the comparison
as `str(9) > "50"`, and `"9" > "50"` is `True`, because string comparison goes
character by character and `"9"` sorts after `"5"` regardless of length. The
function returned "Too High" for a guess that was 41 below the secret.

The part I did not expect was which line was actually to blame for the error. I had assumed
the `str()` cast on line 159 was the bug. The explanation convinced me the real
problem was the `except TypeError` block on line 41: the cast creates the
error, but the `except` hides it and hands back a plausible looking wrong
answer instead. That is why the Console Output column in my bug log says
`none` on all seven rows. The program never complained, because it had been
written not to. 

**A correct suggestion I accepted.** The assistant suggested that `check_guess`
should return a bare outcome string like `"Win"` instead of a tuple, and that
the hint sentence should move into a separate `HINTS` dictionary read by a
`hint_for()` function.

I accepted it for two reasons. First, `tests/test_game_logic.py` already
asserts `check_guess(50, 50) == "Win"`, so a function returning a tuple could
never pass those tests, and editing the starter tests to match my code would
have been backwards. Second, splitting the label from the sentence fixes Bug 1
structurally rather than patching it - the starter had typed the label and the
message out together in six separate places, which is exactly how they drifted
apart. With one lookup table they cannot disagree again.

I verified it by running `pytest`. The three starter tests went from failing
with `NotImplementedError` to passing, and I did not edit a single line of
them. That was my proof the refactor had not broken the original contract.

**A suggestion I did not accept as written.** When the assistant gave me a full
replacement for `logic_utils.py`, I read it before pasting. I found two things
I had not asked for: a `proximity_label()` function that grades guesses as hot
or cold, and a change to the `Hard` difficulty range from `(1, 50)` to
`(1, 200)`. I stopped and asked it to justify the file to me first.

Neither change mapped to any of the four bugs I had logged. `proximity_label`
was a brand new feature, and while the Hard range genuinely is a bug, it
was not a bug I had documented or reproduced. I would have been submitting
changes I could not explain, which is the opposite of what this project was
asking me to practise. I asked for a version limited to the bugs I had actually
found.

This happened to me a second time, harder. In an earlier round I let the
assistant rewrite `logic_utils.py`, `app.py` and the test file in one pass. The
result worked as 42 tests passed, but it had gone well past what I asked for
and I could not account for every change in it. I used `git stash` to roll my
working tree back to my last commit and started again more slowly. I kept it in
the stash rather than deleting it, so I could still read what it had done.

I verified my own narrower version the same way each time: `pytest` (53 tests
passing), `flake8` (0 issues), and a `play_session.py` script that drives the
real app from start to finish.

---

## 3. Debugging and testing your fixes

I decided a bug was really fixed only when I had a test that failed before my
change and passed after it. Writing the assertion first changed the question
from "does this diff look right to me?" into something with a yes or no answer.

The clearest example was the scoring bug. I wrote
`test_bug4_a_wrong_guess_never_pays_points`, parametrized over attempts 1
through 8, asserting that `update_score(50, "Too High", n)` returns 45 every
time. Against the starter it failed on every even-numbered attempt, returning
55 instead. That pinned the bug to one line -
`if attempt_number % 2 == 0: return current_score + 5` - and it matched the
0 to 5 jump I had recorded in my Bug 4 reproduction log exactly.

The more useful thing I learned came from the bugs that unit tests could not
reach. Bugs 2 and 3 do not live in any function - the attempt counter and the
broken New Game button live in Streamlit's session state - so no amount of
testing `logic_utils.py` would ever catch them. For those I used
`streamlit.testing.v1.AppTest`, which runs my real `app.py` without a browser
so I can click the buttons and then assert on `st.session_state` afterwards.
`test_bug3_new_game_after_a_win_resets_every_piece_of_state` wins a round,
clicks New Game, and checks that status, score, attempts and history all reset
together. That was the lesson I want to keep: the layer a bug lives in decides
what kind of test is capable of catching it.

AI right here helped me more with test *coverage* than with test *design*. I described
`parse_guess` and asked what inputs would break it, and it suggested
whitespace-only strings and `None`, which I had not thought about and which
turn out to matter because Streamlit sends an empty string on the very first
page load. It was also wrong at least once. It asserted that `int("٤٢")` would
raise a `ValueError` and be rejected as non-numeric. I ran the test and it
failed - Python accepts Unicode decimal digits, so `int("٤٢")` returns 42. The
AI had asserted behaviour it assumed rather than checked. I dropped the case
instead of writing a special rule for it.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
