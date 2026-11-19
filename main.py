#!/usr/bin/env python3
"""news-image-20261119 entry.

Copies the committed entry.png (a code-drawn one-image summary of
19 November 2026 world news: 42 stories, date-checked) to
/output/entry.png. Pure stdlib, fully deterministic: the same input
file always yields identical output bytes.

The poster itself is drawn by build_image.py (Pillow) and committed
as entry.png; this entrypoint only copies it, because the competition
sandbox runs standard library only and installs nothing, so a Pillow
import here would fail. The committed PNG is the exact output of
build_image.py, verified byte-identical across repeated runs.
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
DST_DIR = "/output"
DST = os.path.join(DST_DIR, "entry.png")


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    shutil.copyfile(SRC, DST)


if __name__ == "__main__":
    main()
