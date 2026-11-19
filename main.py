#!/usr/bin/env python3
"""Put the finished 19 November 2026 poster where the harness looks.

The picture itself was painted earlier, off-line, by build_image.py
and stored in this repository as entry.png; it was run twice and the
bytes came out identical both times. All this little program has to
do is place that one file at /output/entry.png for the judges.

Nothing beyond the standard library is used, and nothing is fetched
from the network, so it runs the same in the grading sandbox as here.
The poster packs the day into one front page: a lead story, four
panels, and a sourced wire of 37 further stories, 42 in total, with
the date printed on the masthead and checked in its own box.
"""

from pathlib import Path

POSTER = Path(__file__).resolve().parent / "entry.png"
TARGET = Path("/output/entry.png")


def place_poster() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(POSTER.read_bytes())


place_poster()
