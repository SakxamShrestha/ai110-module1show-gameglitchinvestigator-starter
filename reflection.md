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

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
