#!/bin/sh
# Build the release patch: the English disc from your Japanese .bin, then an xdelta3 between them.
#   tools/make_xdelta.sh "Rakugaki Showtime (Japan).bin" [OUT_DIR]
# Writes OUT_DIR (default work/release)/rakugaki-showtime-en.xdelta and prints the SHA-1s for the
# README. Needs python3 with Pillow, llvm-mc (Homebrew llvm) and xdelta3.
set -eu
[ $# -ge 1 ] || { sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
SRC=$1
OUT=${2:-$ROOT/work/release}
command -v xdelta3 >/dev/null || { echo "xdelta3 not found (brew install xdelta)" >&2; exit 1; }
mkdir -p "$OUT"
python3 "$ROOT/tools/en_disc.py" "$SRC" "$OUT/english.bin"
xdelta3 -e -9 -f -s "$SRC" "$OUT/english.bin" "$OUT/rakugaki-showtime-en.xdelta"
xdelta3 -d -f -s "$SRC" "$OUT/rakugaki-showtime-en.xdelta" "$OUT/check.bin"
cmp "$OUT/english.bin" "$OUT/check.bin"
rm "$OUT/check.bin"
ls -l "$OUT/rakugaki-showtime-en.xdelta"
shasum "$SRC" "$OUT/english.bin"
