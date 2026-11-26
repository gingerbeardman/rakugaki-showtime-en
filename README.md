# Rakugaki Showtime: English patch

An English patch for **Rakugaki Showtime** (ラクガキショータイム), Treasure / Enix, 1999, PlayStation (SLPM-86272, Japan).

> **The English is machine translated.** Every line is checked to fit its space on screen, which is the major constraint—but it is not a professional translation, and some lines will read oddly.

## What it translates

- Menus, character names, quips and taunts, memory card messages and the other text the game prints in its body font.
- The control tips (Options > Demonstration > ソウサセツメイ).
- The headings and buttons drawn as pictures: MODE SELECT, CHARACTER SELECT, NEXT STAGE, OK? and the rest.
- The big sprite headings and banners: PAUSE, CONTINUE? YES / NO, START! and CLEAR!.

The title logo and FMV stay as they are, for now.

## You need

- Your own copy of the Japanese disc, as a single `.bin` (2352-byte sectors) with its `.cue`. The patch was made against this image:

  | | |
  |---|---|
  | File | `Rakugaki Showtime (Japan).bin` |
  | Size | 591,880,800 bytes |
  | CRC32 | `b96faa9c` |
  | MD5 | `f162a25833bd0fc92e1b0c6da88cdb7a` |
  | SHA-1 | `b648451d4ee6bfa29f56467551d3ec3240e2eebe` |

- An xdelta tool: [xdelta3](https://github.com/jmacd/xdelta), or a front end such as Delta Patcher or xdelta UI. Online patchers such as [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) also take xdelta files.

No disc data comes with this patch.

## Applying the patch

Download `rakugaki-showtime-en.xdelta` from the [Releases](../../releases) page, then:

```sh
xdelta3 -d -s "Rakugaki Showtime (Japan).bin" rakugaki-showtime-en.xdelta "Rakugaki Showtime (English).bin"
```

Copy the `.cue` next to the new `.bin`, and change the `FILE` line in the copy to the new file name. The patched image should be:

| | |
|---|---|
| CRC32 | `97f989b8` |
| SHA-1 | `5a8ac2262e2b9f724fad034c5527bc08cebadef2` |

It has been tested in the RetroArch PCSX ReARMed core.

## Building the patch from source

The patch is built from this repository, and the tool can patch your disc directly in place of the xdelta:

```sh
python3 tools/en_disc.py "Rakugaki Showtime (Japan).cue" "Rakugaki Showtime (English).cue"
```

The input can be a CHD, a cue sheet with its bins, a raw `.bin` or an `.iso`, and the output is written in the same form. Only the changed sectors are rewritten, with fresh EDC/ECC; every file keeps its size and place on the disc. `--report` lists every string with its room and the bytes its English takes.

`tools/make_xdelta.sh "Rakugaki Showtime (Japan).bin"` builds the release xdelta and checks it.

Requirements:
- Python 3 with [Pillow](https://python-pillow.org)
- `llvm-mc` to assemble the new MIPS code (on macOS: `brew install llvm`)
- `chdman` (MAME tools) for CHD input
- `xdelta3` for `make_xdelta.sh`

## How it works

Everything changes in two files: `ARA.BIN` (the main program and its data) and `HAGECHO.BIN` (the stage modules and graphics). Only 69 sectors change.

- **Text.** The game prints 16 px full-width characters only. The text printer and the glyph routine the control tips use are rewritten in MIPS assembly (`tools/en_disc/block.s`, `glyph.s`) to draw ASCII in a proportional 8 px half-width font, so English fits in the space the Japanese had. The font goes into the font sheet's hiragana cells, which no English text needs. Full-width A–Z, digits, katakana and symbols still work.
- **Strings** (`translations/en.tsv`) are rewritten in place. The `disc` column holds a shorter English where a line has no more room than its Japanese bytes. The control tips (`translations/training.tsv`) are repacked into their own space and their line pointers moved.
- **Word pictures** (`translations/ui/en/*.png`) are written over the Japanese ones at the same size, where `translations/ui/words.tsv` says they are on the disc.
- **Big headings and banners** are lettered into the sprite frames only they use, and their tables rewritten.

## The lettering

The patch brings no outside font. Both letterings come from the game:

- **The 8 px text font** (`tools/halfwidth.py`) is cut from the game's own 16 px font, read from your disc as the patch is built. Each glyph is trimmed to its width across the font's four hand-drawn "scribble" frames, so English text wobbles like the Japanese. Glyphs wider than 7 px are narrowed by merging columns, and the few characters the game lacks are drawn to match.
- **The headings and buttons** (`tools/ui_lettering.py`) follow the game's own English lettering, the 8 px letters of PRESS SELECT + START TO EXIT on the character select. Eleven letters are the game's; the rest are drawn to match. For the 16 px slots they are doubled, narrowed to fit, and kerned with a 1 px gap. The big headings are lettered in the same style.

## Changing the translation

```sh
python3 tools/disc_files.py "Rakugaki Showtime (Japan).cue"   # ARA.BIN, HAGECHO.BIN, DO.BIN into work/disc
python3 tools/ui_words.py extract                             # the Japanese word pictures into work/ui/ja
```

- **Body text:** edit `translations/en.tsv` or `training.tsv` and rebuild. The build stops and says which line is too long.
- **A word picture:** edit its `english` in `translations/ui/words.tsv`, then `python3 tools/ui_words.py draft ID` letters it into `translations/ui/en/ID.png`. You can also draw the PNG by hand: an indexed PNG at the slot's size, in the slot's palette. `ui_words.py sheet` puts each word's Japanese and English side by side in `work/ui/sheet.png`, and `ui_words.py alphabet` shows every letter of the lettering.

`work/` holds the game's own data and stays out of git.

## Contributing

I'm not accepting pull requests at the moment. You're welcome to fork the repository and make your own version under the licence below.

## Licence

The tools and translation files are under the MIT licence (`LICENSE`).

Rakugaki Showtime is © Treasure / Enix 1999. This is an unofficial fan translation with no connection to Treasure, Square Enix or Sony. It contains no game data: you need your own disc.
