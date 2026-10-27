"""Write today's Chained puzzle into README.md, between the chained-today markers.

    python scripts/chained_today.py

Reads the public /api/puzzle/today endpoint, which returns only the first letter of
each word, so nothing here spoils the answers. If the request fails for any reason,
the line falls back to a plain link, so the README never shows a stale puzzle.
Uses only the standard library, so the GitHub Action needs no setup step.
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

README = pathlib.Path(__file__).resolve().parent.parent / "README.md"
API = os.environ.get("CHAINED_API_URL", "https://playchained.me/api/puzzle/today")
EPOCH = dt.date(2026, 9, 21)  # puzzle #1, same as PUZZLE_EPOCH in the Chained backend
START, END = "<!-- chained-today:start -->", "<!-- chained-today:end -->"
FALLBACK = "Today's chain is up at **[playchained.me](https://playchained.me)**."


def fetch_line(today: dt.date) -> str:
    req = urllib.request.Request(API, headers={"User-Agent": "AhmedM240-profile-readme"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    words = sorted(data["words"], key=lambda w: w["position"])
    letters = [str(w["first_letter"]).strip().upper()[:1] for w in words]
    if not letters or not all(ch.isalpha() for ch in letters):
        raise ValueError(f"unexpected puzzle data: {data!r}")
    number = (today - EPOCH).days + 1
    chain = " → ".join(f"`{ch}`" for ch in letters)
    return (f"**Today's [Chained](https://playchained.me) · #{number}** &nbsp; {chain} &nbsp; "
            f"<sub>{len(letters)} words, first letters only · [solve it](https://playchained.me)</sub>")


def main() -> int:
    today = dt.datetime.now(dt.timezone.utc).date()  # Chained resets at midnight UTC
    try:
        line = fetch_line(today)
    except Exception as exc:  # network error, 404 before a puzzle exists, bad JSON...
        print(f"warning: could not read today's puzzle ({exc}); using the fallback line", file=sys.stderr)
        line = FALLBACK

    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        print("error: README.md is missing the chained-today markers", file=sys.stderr)
        return 1
    new = pattern.sub(lambda _: f"{START}\n{line}\n{END}", text)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("updated:", line)
    else:
        print("no change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
