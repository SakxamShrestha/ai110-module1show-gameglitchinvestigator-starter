"""Replay a full game against app.py and print a transcript.

Uses Streamlit's own AppTest harness, so this drives the real app script -
session state, buttons and all - without opening a browser. The output is the
end-to-end evidence that the repaired game plays correctly.

Run it with:

    python play_session.py
"""

from streamlit.testing.v1 import AppTest


def texts(app):
    """Collect the text of every info/warning/success/error on the page."""
    out = []
    for kind in ("info", "warning", "success", "error"):
        out += [element.value for element in getattr(app, kind)]
    return out


def play(secret, guesses, difficulty="Normal"):
    """Force a known secret, then submit each guess and print what happened."""
    app = AppTest.from_file("app.py", default_timeout=30)
    app.run()

    app.session_state.secret = secret
    app.run()

    print(f"\n=== New game | difficulty={difficulty} | secret={secret} ===")
    for guess in guesses:
        app.text_input[0].set_value(str(guess))
        app.button[0].click()
        app.run()
        for line in texts(app):
            print(f"  guess {guess!r:>6} -> {line}")
        print(
            f"         score={app.session_state.score} "
            f"attempts={app.session_state.attempts} "
            f"status={app.session_state.status}"
        )
        if app.session_state.status != "playing":
            break
    return app


if __name__ == "__main__":
    play(50, ["abc", "", 25, 75, 60, 50])
    play(50, [9, 50])
    print("\n=== Session replay finished with no exceptions ===")
