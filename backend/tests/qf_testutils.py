"""Helpers shared by the test modules (named to avoid clashing with a site-packages `tests`)."""


def scores(value, feedback="ok"):
    return {
        "correctness": value, "completeness": value, "safety": value,
        "actionability": value, "clarity": value, "feedback": feedback,
    }
