import re
from functools import lru_cache


@lru_cache(maxsize=None)
def _pattern(keyword: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(keyword.lower())}\b")


def contains_keyword(text: str, keywords) -> bool:
    """Whole-word/phrase match, so "app" doesn't hit "happy" or "how" hit "show"."""
    text = text.lower()
    return any(_pattern(k).search(text) for k in keywords)
