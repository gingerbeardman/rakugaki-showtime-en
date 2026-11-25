#!/usr/bin/env python3
"""Copy the files the patch works on out of your Japanese disc, for the authoring tools.

  tools/disc_files.py IN [DIR]

IN is the disc as a CHD, a cue sheet, a raw .bin or an .iso (as tools/en_disc.py takes). Writes
ARA.BIN, HAGECHO.BIN and DO.BIN into DIR (default work/disc). CHD needs chdman (MAME).
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en_disc  # noqa: E402

NAMES = ("ARA.BIN", "HAGECHO.BIN", "DO.BIN")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    inp = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else en_disc.ROOT / "work" / "disc"
    with tempfile.TemporaryDirectory() as td:
        ext = inp.suffix.lower()
        if ext == ".chd":
            if not shutil.which("chdman"):
                en_disc.die("chdman not found (MAME tools)")
            subprocess.run(["chdman", "extractcd", "-i", str(inp), "-o", f"{td}/d.cue", "-ob", f"{td}/d.bin"],
                           check=True, capture_output=True)
            track = Path(td) / "d.bin"
        elif ext == ".cue":
            fl = en_disc.parse_cue(inp)
            if not fl:
                en_disc.die(f"{inp}: no FILE in the cue sheet")
            track = inp.parent / fl[0][0]
        else:
            track = inp
        t = en_disc.Track(track)
        out.mkdir(parents=True, exist_ok=True)
        for n in NAMES:
            if n not in t.files:
                en_disc.die(f"no {n}: not Rakugaki Showtime (SLPM-86272)?")
            (out / n).write_bytes(t.read(n))
    print(f"{out}: {', '.join(NAMES)}")


if __name__ == "__main__":
    main()
