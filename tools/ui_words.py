#!/usr/bin/env python3
"""English UI words: the game's pre-drawn word pictures (headings, buttons) and their English versions.

The game draws headings and buttons (キャラクター, セレクト, オーケー？ ...) as one 4bpp texture quad per
word, from pages such as VRAM 704,0. The disc patch (tools/en_disc.py) writes an English picture of the same
size over each one. The pictures are indexed PNGs whose pixel values are the palette indices the
game's CLUT colours. translations/ui/words.tsv lists every word picture the game has.

  extract [--disc DIR]
      The Japanese word pictures, each as work/ui/ja/<id>.png (the game's art: not committed), read
      from DIR/HAGECHO.BIN (default work/disc: tools/disc_files.py puts the disc's files there) where
      words.tsv's disc column says they are. work/ui/sheet.png shows them all with their ids.
      Rows whose english is "-" are not words and stay out of the sheet.
  draft [--squeeze F] [--gap PX] [--font FILE] [--force] [--en-dir DIR --sheet FILE] [ID ...]
      Letters each row's english into translations/ui/en/<id>.png at the word's size, in its main
      palette index. The lettering is the game's own English style (tools/ui_lettering.py): 8 px
      slots get its 8 px letters as drawn; 16 px slots its 16 px letters, every one squeezed alike:
      --squeeze (default the widest of 100%, 95% ... 50% at which every word fits its slot) and
      --gap clear pixels between letters (default 1), so headings match.
      --font FILE letters with a TTF instead, with --slant and --cap. Existing PNGs are kept unless
      --force (or named).
  alphabet [--squeeze F]
      work/ui/alphabet.png: the 16 px lettering's every character, enlarged, to check new letters.
  locate [--disc DIR]
      Finds each word's Japanese texels (work/ui/ja) on the disc (DIR/HAGECHO.BIN, default work/disc)
      and writes where into the disc column, for the disc patch (tools/en_disc.py).
  sheet [--en-dir DIR] [--sheet FILE]
      work/ui/sheet.png: each word's Japanese and English side by side. --en-dir and --sheet (draft too)
      draw into a scratch folder instead, to compare fonts without touching translations/ui/en.

words.tsv columns: id, tpx, tpy, u, v, w, h, hash, clut (16 colours, hex), english, align, disc, note.
disc: the picture's first row in HAGECHO.BIN and the bytes from one row to the next (offset/stride, hex).
align: c (default) centres the English in its slot; r and l push it to the right or left edge, for a
heading the game draws from two pictures side by side (CHARACTER | SELECT) so the words meet.
"""

import argparse
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python3 -I leaves it out
import ui_lettering  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work" / "ui"
UI = ROOT / "translations" / "ui"
TSV = UI / "words.tsv"
EN = UI / "en"
JA = WORK / "ja"
DISC = ROOT / "work" / "disc"
COLS = ["id", "tpx", "tpy", "u", "v", "w", "h", "hash", "clut", "english", "align", "disc", "note"]


def fnv(vals):
    h = 2166136261
    for x in vals:
        h = ((h ^ x) * 16777619) & 0xFFFFFFFF
    return h


def palette(clut_hex):
    """16 PS1 colours -> PNG palette (index 0 shown as dark grey: it is transparent in the game)."""
    pal = []
    for i in range(16):
        c = int(clut_hex[i * 4:i * 4 + 4], 16)
        r, g, b = (c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3
        pal += [40, 40, 40] if i == 0 else [r, g, b]
    return pal + [0, 0, 0] * 240


def indexed(w, h, texels, clut_hex):
    im = Image.new("P", (w, h))
    im.putpalette(palette(clut_hex))
    im.putdata(texels)
    im.info["transparency"] = 0
    return im


def read_rows():
    if not TSV.exists():
        return []
    with TSV.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader((ln for ln in f if not ln.startswith("#")), delimiter="\t")
        return [dict(row) for row in r]


def write_rows(rows):
    UI.mkdir(parents=True, exist_ok=True)
    with TSV.open("w", encoding="utf-8", newline="") as f:
        f.write("# English UI words (tools/ui_words.py): fill in english, or - for a quad that is not a word.\n")
        w = csv.DictWriter(f, COLS, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def cmd_extract(a):
    hag = (Path(a.disc) / "HAGECHO.BIN").read_bytes()
    JA.mkdir(parents=True, exist_ok=True)
    n = 0
    for r in read_rows():
        if r["english"] in ("", "-") or not r.get("disc"):
            continue
        w, h = int(r["w"]), int(r["h"])
        off, stride = (int(x, 16) for x in r["disc"].split(",")[0].split("/"))
        tex = []
        for y in range(h):
            for b in hag[off + y * stride:off + y * stride + w // 2]:
                tex += [b & 15, b >> 4]
        if fnv(tex) != int(r["hash"], 16):
            print(f"{r['id']} ({r['english']}): the texels on this disc differ")
        indexed(w, h, tex, r["clut"]).save(JA / f"{r['id']}.png")
        n += 1
    print(f"{n} pictures in {JA.relative_to(ROOT)}")
    cmd_sheet(a)


def lettering(text, font_file, slant, cap):
    """The text as a 1-bit mask (L, 0/255), its capitals `cap` px tall, slanted like the game's
    lettering and cropped to its ink; every word shares the size, so headings match."""
    size = 8
    for s in range(8, 64):
        b = ImageFont.truetype(font_file, s).getbbox("HX")
        if b[3] - b[1] > cap:
            break
        size = s
    ft = ImageFont.truetype(font_file, size)
    hb, tb = ft.getbbox("HX"), ft.getbbox(text)
    h = cap + 4
    m = Image.new("L", (tb[2] - tb[0] + int(h * slant) + 4, h), 0)
    ImageDraw.Draw(m).text((-tb[0] + int(h * slant) + 2, 2 - hb[1]), text, font=ft, fill=255)
    if slant:   # x' = x - slant*(y - h): leans right like the game's lettering
        m = m.transform(m.size, Image.AFFINE, (1, slant, -slant * h, 0, 1, 0), resample=Image.NEAREST)
    m = m.point(lambda p: 255 if p > 110 else 0)
    box = m.getbbox()
    return m.crop(box) if box else m


def place(mask, w, h, fill, align="c"):
    """The mask in a w x h slot (align c, l or r, 1 px in from the edge; cut to fit if too big);
    palette index `fill`."""
    if mask.width > w or mask.height > h:
        mask = mask.resize((min(w, mask.width), min(h, mask.height)), Image.BILINEAR).point(lambda p: 255 if p > 110 else 0)
    out = Image.new("L", (w, h), 0)
    x = {"l": 1, "r": w - 1 - mask.width}.get(align, (w - mask.width) // 2)
    out.paste(mask, (max(0, x), (h - mask.height) // 2))
    return [fill if p else 0 for p in out.tobytes()]


def word_masks(rows, a):
    """{id: L mask} for every row, and a note on the size: the game's lettering (one squeeze that fits
    every slot unless --squeeze) or, with --font, a TTF at one cap height and one squeeze."""
    if a.font:
        cap = a.cap or min(int(r["h"]) for r in rows) - 2
        masks = {r["id"]: lettering(r["english"], a.font, a.slant, cap) for r in rows}
        xs = min([1.0] + [(int(r["w"]) - 2) / masks[r["id"]].width for r in rows])
        return {k: squeezed(m, xs) for k, m in masks.items()}, f"{Path(a.font).name}, capitals {cap} px, squeezed to {xs:.0%}"
    small = [r for r in rows if int(r["h"]) < ui_lettering.H]      # 8 px slots: the letters as drawn
    rows = [r for r in rows if r not in small]
    g8 = ui_lettering.glyphs8()
    def setall(f):
        g = ui_lettering.glyphs(f)
        return {**{r["id"]: ui_lettering.setword(r["english"], g, a.gap) for r in rows},
                **{r["id"]: ui_lettering.setword(r["english"], g8, a.gap) for r in small}}
    fits = lambda ws: all(len(ws[r["id"]][0]) <= int(r["w"]) - 2 for r in rows) and \
        all(len(ws[r["id"]][0]) <= int(r["w"]) for r in small)
    if a.squeeze:
        f, words = a.squeeze, setall(a.squeeze)
    else:
        for f in [x / 100 for x in range(100, 45, -5)]:
            words = setall(f)
            if fits(words):
                break
    masks = {}
    for k, w in words.items():
        m = Image.new("L", (len(w[0]), len(w)), 0)
        m.putdata([255 if c == "#" else 0 for row in w for c in row])
        masks[k] = m
    return masks, f"the game's lettering, squeezed to {f:.0%}, gap {a.gap}" + ("" if fits(words) else " (some words too wide: cut to fit)")


def squeezed(mask, xscale):
    if xscale >= 1:
        return mask
    return mask.resize((max(1, round(mask.width * xscale)), mask.height), Image.BILINEAR).point(lambda p: 255 if p > 110 else 0)


def cmd_draft(a):
    rows = [r for r in read_rows() if r["english"] and r["english"] != "-"]
    en = Path(a.en_dir) if a.en_dir else EN
    en.mkdir(parents=True, exist_ok=True)
    masks, note = word_masks(rows, a)
    n = 0
    for r in rows:
        if a.ids and r["id"] not in a.ids:
            continue
        dst = en / f"{r['id']}.png"
        if dst.exists() and not (a.force or a.ids):
            continue
        w, h = int(r["w"]), int(r["h"])
        ja = JA / f"{r['id']}.png"
        fill = 15
        if ja.exists():
            vals = [p for p in Image.open(ja).tobytes() if p]
            if vals:
                fill = max(set(vals), key=vals.count)
        indexed(w, h, place(masks[r["id"]], w, h, fill, (r.get("align") or "c").strip()), r["clut"]).save(dst)
        n += 1
    print(f"{n} drafts in {en} ({note})")
    cmd_sheet(a)


def cmd_alphabet(a):
    g = ui_lettering.glyphs(a.squeeze or 1.0)
    cell, cols, s = 22, 11, 4
    nrow = (len(ui_lettering.ORDER) + cols - 1) // cols
    im = Image.new("RGB", (cols * cell * s, nrow * cell * s), (28, 28, 28))
    d = ImageDraw.Draw(im)
    for k, ch in enumerate(ui_lettering.ORDER):
        r = g[ch]
        gx, gy = (k % cols) * cell * s, (k // cols) * cell * s
        ox = (cell - len(r[0])) // 2
        ink = (200, 200, 60) if ch in ui_lettering.GAME else (60, 160, 40)
        for y, row in enumerate(r):
            for x, c in enumerate(row):
                if c == "#":
                    d.rectangle([gx + (ox + x) * s, gy + (4 + y) * s, gx + (ox + x + 1) * s - 1, gy + (5 + y) * s - 1], fill=ink)
        d.text((gx + 3, gy + 1), ch, fill=(150, 150, 150))
    out = WORK / "alphabet.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    print(f"{out}: yellow letters are the game's own, green drawn to match")


def cmd_locate(a):
    hag = (Path(a.disc) / "HAGECHO.BIN").read_bytes()
    rows = read_rows()
    n = 0
    for r in rows:
        if r["english"] in ("", "-") or not (JA / f"{r['id']}.png").exists():
            continue
        w, h = int(r["w"]), int(r["h"])
        px = Image.open(JA / f"{r['id']}.png").tobytes()
        if w % 2 or int(r["u"]) % 2:
            print(f"{r['id']}: not byte-aligned, skipped")
            continue
        lines = [bytes(px[y * w + x] | (px[y * w + x + 1] << 4) for x in range(0, w, 2)) for y in range(h)]
        y0 = max(range(h), key=lambda y: len(set(lines[y])))
        found, p = [], -1
        while True:
            p = hag.find(lines[y0], p + 1)
            if p < 0:
                break
            for stride in range(w // 2, 2049, 2):
                b = p - y0 * stride
                if b >= 0 and all(hag[b + y * stride:b + y * stride + w // 2] == lines[y] for y in range(h)):
                    found.append(f"{b:x}/{stride:x}")
                    break
        r["disc"] = ",".join(dict.fromkeys(found))
        n += bool(found)
        if not found:
            print(f"{r['id']} ({r['english']}): not found on the disc")
    write_rows(rows)
    print(f"{TSV.relative_to(ROOT)}: {n} words located")


def cmd_sheet(a):
    en = Path(getattr(a, "en_dir", None) or EN)
    out = Path(getattr(a, "sheet", None) or WORK / "sheet.png")
    rows = [r for r in read_rows() if r["english"] != "-"]
    if not rows:
        return
    scale, pad = 3, 6
    cw = max(int(r["w"]) for r in rows) * 2 + 24       # Japanese, then English, then the label
    lh = max(int(r["h"]) for r in rows) + pad
    sheet = Image.new("RGB", (cw + 200, lh * len(rows) + pad), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for k, r in enumerate(rows):
        y = pad + k * lh
        for col, p in ((0, JA / f"{r['id']}.png"), (int(r["w"]) + 12, en / f"{r['id']}.png")):
            if p.exists():
                sheet.paste(Image.open(p).convert("RGB"), (4 + col, y))
        d.text((cw + 4, y + 2), f"{r['id']}  {r['english']}", fill=(200, 200, 200))
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)   # labels scale too: still legible
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"{out}: {len(rows)} words")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = p.add_subparsers(dest="cmd", required=True)
    e = sp.add_parser("extract")
    e.add_argument("--disc", default=str(DISC))
    dr = sp.add_parser("draft")
    dr.add_argument("--squeeze", type=float, help="letter width, 0.5-1 (default: the widest that fits every slot)")
    dr.add_argument("--gap", type=int, default=1, help="clear pixels between letters (default 1)")
    dr.add_argument("--font", help="letter with this TTF instead")
    dr.add_argument("--force", action="store_true")
    dr.add_argument("--slant", type=float, default=0.25, help="--font only")
    dr.add_argument("--cap", type=int, help="--font only: capital height in px (default: the shortest slot less 2)")
    dr.add_argument("--en-dir", help="write the drafts here instead of translations/ui/en (to compare fonts)")
    dr.add_argument("--sheet", help="the contact sheet's path (default work/ui/sheet.png)")
    dr.add_argument("ids", nargs="*")
    lo = sp.add_parser("locate")
    lo.add_argument("--disc", default=str(DISC))
    al = sp.add_parser("alphabet")
    al.add_argument("--squeeze", type=float)
    sh = sp.add_parser("sheet")
    sh.add_argument("--en-dir", help="the English pictures to show (default translations/ui/en)")
    sh.add_argument("--sheet", help="its path (default work/ui/sheet.png)")
    a = p.parse_args()
    {"extract": cmd_extract, "draft": cmd_draft, "alphabet": cmd_alphabet, "locate": cmd_locate, "sheet": cmd_sheet}[a.cmd](a)


if __name__ == "__main__":
    main()
