#!/usr/bin/env python3
"""English patch for the original Rakugaki Showtime disc (SLPM-86272).

  tools/en_disc.py IN OUT [--report]

IN is the Japanese disc as a CHD, a cue sheet (cue/bin, one bin or one per track), a raw .bin
(2352-byte sectors) or an .iso (2048-byte sectors). OUT is written in the same form: OUT.chd, OUT.cue
with its bins, OUT.bin or OUT.iso. Every file keeps its size and place, so the disc layout and the
audio and movie tracks are untouched. Changed sectors get new EDC/ECC. CHD needs chdman (MAME);
assembling the code needs llvm-mc (Homebrew llvm).

What changes (all in ARA.BIN, the main program and its data, and HAGECHO.BIN, the stage modules):
- The text printer (f_80043348) and the glyph routine the training tips use (f_8003ce18) are
  rewritten (tools/en_disc/block.s, glyph.s) to draw ASCII in an 8 px half-width font. The font is
  made from the disc's own 16 px font (tools/halfwidth.py) into the sheet's hiragana cells, which no
  English text needs; full-width A-Z, digits, katakana and symbols stay.
- Every string in translations/en.tsv is rewritten in place (its disc column when the English is
  too long for the string's room), aligned as that file says. The training tips
  (translations/training.tsv) are repacked into their own space and their line pointers moved.
- The heading and button pictures become translations/ui/en/*.png.
- The big sprite headings (pause, continue) and banners (start, clear) are lettered from the
  game-style alphabet (tools/ui_lettering.py big_glyph) into the frames they alone use, and their
  tables rewritten.

--report lists every string with its room and the bytes the English takes.
"""

import argparse
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import halfwidth  # noqa: E402

TSV = ROOT / "translations" / "en.tsv"
TRAINING = ROOT / "translations" / "training.tsv"
UI = ROOT / "translations" / "ui"
ASM = ROOT / "tools" / "en_disc"

# The files of the one disc this patch knows (SHA-1 of the Japanese release's files).
KNOWN = {"ARA.BIN": "32be2f3991efcf80954797f38a70a1bc2511b1c4", "HAGECHO.BIN": "ea5560ab84169f089e4ae134c63c875a2b91ad31"}

IMAGE = 0x3A000           # ARA.BIN: the main program image (loaded at 0x80010000) starts here
BASE = 0x80010000
BLOCK = 0x800430DC        # the printer chain, 0x800430dc..0x800433d0
BLOCK_END = 0x800433D0
GLYPH = 0x8003CE18        # f_8003ce18, 76 instructions
GLYPH_END = 0x8003CF48
F_QUAD = 0x80042F28       # adds a 16x16 font quad to the OT
COLOURS = 0x800A4EBC      # printer colour index -> rgb word
TABLES = 0x800310A8       # the old punctuation jump table (180 words): the new tables go here
ADV = TABLES              # 96 bytes: advance in px of ASCII 0x20 + i
PUNCT = TABLES + 96       # 180 bytes: SJIS 0x8141 + i -> cell (was the jump table's targets)
RANGES = TABLES + 276     # the mapper's SJIS ranges: lo - 0x8000, count, first cell (as f_800430dc had)
MAP_RANGES = [(0x824F, 10, 0), (0x8260, 26, 17), (0x8281, 26, 49), (0x829F, 83, 80), (0x8340, 63, 163),
              (0x8380, 23, 226), (0x8141, 0, 0)]
SHEET = 0x34BB8           # HAGECHO entry 0: the 16x16 font sheet, 256 rows of 128 bytes
HALF_ROW = 5              # the half-width glyphs go into cell rows 5..7 (hiragana)
TRAIN_ENTRY, TRAIN_BASE = 5, 0x8012BCD0     # entry 5 (s05dm) and where it loads
TRAIN_PAGES, TRAIN_NPAGES = 0x801343A8, 14  # page table: page -> 0-terminated list of line pointers
SEC = 2352


def die(msg):
    sys.exit(f"en_disc: {msg}")


# ---- the disc ----------------------------------------------------------------------------------

def _edc_table():
    t = []
    for i in range(256):
        e = i
        for _ in range(8):
            e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
        t.append(e)
    return t


_EDC = _edc_table()
_ECC_F = [((i << 1) ^ (0x11D if i & 0x80 else 0)) & 0xFF for i in range(256)]
_ECC_B = [0] * 256
for _i in range(256):
    _ECC_B[_i ^ _ECC_F[_i]] = _i


def _edc(data):
    e = 0
    for b in data:
        e = (e >> 8) ^ _EDC[(e ^ b) & 0xFF]
    return e


def _ecc(sec, major_count, minor_count, major_mult, minor_inc, dest):
    src = sec[0xC:]
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = b = 0
        for _ in range(minor_count):
            t = src[index]
            index += minor_inc
            if index >= size:
                index -= size
            a ^= t
            b ^= t
            a = _ECC_F[a]
        a = _ECC_B[_ECC_F[a] ^ b]
        sec[dest + major] = a
        sec[dest + major + major_count] = a ^ b


def fix_sector(sec):
    """New EDC/ECC for a raw sector (bytearray of 2352) after its user data changed."""
    mode = sec[15]
    if mode == 1:
        struct.pack_into("<I", sec, 0x810, _edc(sec[0:0x810]))
        sec[0x814:0x81C] = bytes(8)
        _ecc(sec, 86, 24, 2, 86, 0x81C)
        _ecc(sec, 52, 43, 86, 88, 0x8C8)
    elif mode == 2 and not sec[18] & 0x20:            # mode 2 form 1: the header counts as zero
        struct.pack_into("<I", sec, 0x818, _edc(sec[16:0x818]))
        hdr = bytes(sec[12:16])
        sec[12:16] = bytes(4)
        _ecc(sec, 86, 24, 2, 86, 0x81C)
        _ecc(sec, 52, 43, 86, 88, 0x8C8)
        sec[12:16] = hdr
    else:
        die("a file to patch sits in a form 2 sector")


class Track:
    """The data track: a raw (2352) or cooked (2048) image file, read and patched by file name."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = bytearray(self.path.read_bytes())
        sync = b"\x00" + b"\xff" * 10 + b"\x00"
        self.raw = self.data[:12] == sync
        if not self.raw and len(self.data) % 2048:
            die(f"{path}: neither 2352-byte sectors nor an ISO")
        self.ss = SEC if self.raw else 2048
        self.off = (24 if self.data[15] == 2 else 16) if self.raw else 0
        self.files = self._dir(*self._root())
        self.dirty = set()

    def user(self, lba):
        o = lba * self.ss + self.off
        return self.data[o:o + 2048]

    def _root(self):
        pvd = self.user(16)
        if pvd[1:6] != b"CD001":
            die("no ISO 9660 volume")
        rec = pvd[156:190]
        return struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]

    def _dir(self, lba, size):
        out = {}
        buf = b"".join(self.user(lba + i) for i in range((size + 2047) // 2048))
        i = 0
        while i < len(buf):
            n = buf[i]
            if n == 0:
                i = (i // 2048 + 1) * 2048
                continue
            ext, ln, fl, nl = struct.unpack_from("<I", buf, i + 2)[0], struct.unpack_from("<I", buf, i + 10)[0], buf[i + 25], buf[i + 32]
            name = buf[i + 33:i + 33 + nl].decode("ascii", "replace").split(";")[0]
            if name not in ("\x00", "\x01") and not fl & 2:
                out[name] = (ext, ln)
            i += n
        return out

    def read(self, name):
        lba, size = self.files[name]
        return bytes(b"".join(self.user(lba + i) for i in range((size + 2047) // 2048))[:size])

    def write(self, name, new):
        lba, size = self.files[name]
        old = self.read(name)
        if len(new) != size:
            die(f"{name}: size changed")
        for i in range(0, size, 2048):
            if new[i:i + 2048] != old[i:i + 2048]:
                chunk = new[i:i + 2048]
                o = (lba + i // 2048) * self.ss + self.off
                self.data[o:o + len(chunk)] = chunk
                self.dirty.add(lba + i // 2048)

    def save(self, path):
        if self.raw:
            for lba in self.dirty:
                o = lba * SEC
                s = bytearray(self.data[o:o + SEC])
                fix_sector(s)
                self.data[o:o + SEC] = s
        Path(path).write_bytes(self.data)


def check_ecc(track):
    """The EDC/ECC code against a sector the disc already has: they must agree."""
    if not track.raw:
        return
    lba = track.files["ARA.BIN"][0]
    s = bytearray(track.data[lba * SEC:(lba + 1) * SEC])
    want = bytes(s)
    fix_sector(s)
    if bytes(s) != want:
        die("EDC/ECC self-check failed")


def parse_cue(cue):
    files, cur = [], None
    for ln in Path(cue).read_text(errors="replace").splitlines():
        m = re.match(r'\s*FILE\s+"(.+)"\s+(\S+)', ln) or re.match(r"\s*FILE\s+(\S+)\s+(\S+)", ln)
        if m:
            cur = [m.group(1), []]
            files.append(cur)
        m = re.match(r"\s*TRACK\s+(\d+)\s+(\S+)", ln)
        if m and cur:
            cur[1].append((int(m.group(1)), m.group(2)))
    return files


# ---- the patch ---------------------------------------------------------------------------------

def llvm_mc():
    for p in [shutil.which("llvm-mc"), "/opt/homebrew/opt/llvm/bin/llvm-mc", "/usr/local/opt/llvm/bin/llvm-mc"]:
        if p and os.path.exists(p):
            return p
    die("llvm-mc not found (brew install llvm)")


def assemble(src, origin, syms):
    """src assembled at origin with the given absolute symbols; returns (bytes, {label: address})."""
    mc = llvm_mc()
    objcopy = str(Path(mc).with_name("llvm-objcopy"))
    nm = str(Path(mc).with_name("llvm-nm"))
    labels = {}
    with tempfile.TemporaryDirectory() as td:
        for _ in range(2):      # once for the labels, once with them
            text = "".join(f".equ {k}, {v:#x}\n" for k, v in {**syms, **{f"ABS_{k}": v for k, v in labels.items()}}.items())
            if not labels:      # first pass: any address will do
                text += "".join(f".equ ABS_{k}, {origin:#x}\n" for k in re.findall(r"^(\w+):", src.read_text(), re.M))
            text += src.read_text()
            s, o, b = Path(td, "a.s"), Path(td, "a.o"), Path(td, "a.bin")
            s.write_text(text)
            r = subprocess.run([mc, "-triple=mipsel-unknown-none", "-mcpu=mips1", "-filetype=obj", str(s), "-o", str(o)],
                               capture_output=True, text=True)
            if r.returncode:
                die(f"{src.name}: {r.stderr}")
            out = subprocess.run([nm, "--defined-only", str(o)], capture_output=True, text=True).stdout
            labels = {}
            for ln in out.splitlines():
                v, t, name = ln.split()
                if t.lower() == "t":
                    labels[name] = origin + int(v, 16)
            subprocess.run([objcopy, "-O", "binary", "--only-section=.text", str(o), str(b)], check=True)
            code = b.read_bytes()
    return code, labels


def read_tsv(path, ncols):
    rows = []
    for n, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip() or ln.startswith("#"):
            continue
        f = ln.split("\t")
        rows.append((n, f + [""] * (ncols - len(f))))
    return rows


def enc(s):
    """English text -> disc bytes: ASCII as is (half-width), anything else SJIS (full-width)."""
    return b"".join(ch.encode("ascii") if ord(ch) < 0x80 else ch.encode("cp932") for ch in s)


def text_width(b, adv):
    w = i = 0
    while i < len(b):
        c = b[i]
        if c == 9:
            w = (w // 16 + 1) * 16
        elif 0x20 <= c < 0x80:
            w += adv[c - 0x20]
        elif c >= 0x80:
            w += 16
            i += 1
        i += 1
    return w


def is_text_before(d, p):
    """A string match at p is really the tail of a longer string (the bytes before are SJIS kana)."""
    if p < 2:
        return False
    try:
        c = d[p - 2:p].decode("cp932")
    except UnicodeDecodeError:
        return False
    return len(c) == 1 and ("぀" <= c <= "ヿ" or "！" <= c <= "～" or c in "ー　、。！？")


def find_strings(d, jb):
    """Places of the 0-terminated SJIS string jb in d, each with its room (bytes the English may use,
    leaving one 0): the 0 bytes after it up to the next 4-byte boundary (where the next string or
    field may start), never past a byte that is not 0."""
    out, p = [], -1
    while True:
        p = d.find(jb + b"\0", p + 1)
        if p < 0:
            return out
        if is_text_before(d, p):
            continue
        end = p + len(jb)
        z = 0
        while end + z < len(d) and d[end + z] == 0:
            z += 1
        z = min(z, ((end + 4) & ~3) - end)
        out.append((p, len(jb) + z - 1))


def build_strings(files, adv, report):
    """Rewrites every en.tsv string in place. Returns the problems (too long, not found)."""
    probs = []
    for n, (ja, en, align, disc) in ((n, f[:4]) for n, f in read_tsv(TSV, 4)):
        if en == "=":
            continue
        jb = ja.encode("cp932")
        txt = enc((disc or en).replace("\\t", "\t").replace("\\\\", "\\"))
        align = align.strip() or "l"
        box, w = len(jb) * 8, text_width(txt, adv)
        off = {"c": (box - w) // 2, "r": box - w}.get(align, 0)
        hits = [(name, p, room) for name in ("ARA.BIN", "HAGECHO.BIN") for p, room in find_strings(files[name], jb)]
        if not hits:
            probs.append(f"en.tsv:{n}: {ja} not found on the disc")
            continue
        for name, p, room in hits:
            body = (bytes([1, max(1, min(255, off + 128))]) if off else b"") + txt
            if len(body) > room:                 # no room for the offset: spaces (4 px each) instead
                body = b" " * max(0, min(room - len(txt), (off + 2) // 4)) + txt
            if len(body) < len(jb):
                body += b"\x02" * (len(jb) - len(body))   # padding: the same length as the Japanese
            if report:
                print(f"{name}\t{p:#x}\t{len(jb)}\t{room}\t{len(body)}\t{ja}\t{disc or en}")
            if len(body) > room:
                probs.append(f"en.tsv:{n}: {ja}: the English takes {len(body)} bytes, the room is {room} ({name} {p:#x})")
                continue
            d = files[name]
            d[p:p + room + 1] = body + bytes(room + 1 - len(body))
    return probs


def train_units(s):
    """A training line (english with {codes}) -> its bytes: text in 2-byte units, odd runs padded
    with a space so every code starts a unit."""
    out, parts = b"", re.split(r"(\{[01][0-9A-Z]\})", s)
    for i, part in enumerate(parts):
        if re.fullmatch(r"\{[01][0-9A-Z]\}", part):
            if len(out) % 2:      # a code starts a unit: move the space after it before it, or add one
                nxt = parts[i + 1] if i + 1 < len(parts) else ""
                if nxt.startswith(" "):
                    parts[i + 1] = nxt[1:]
                out += b" "
            out += part[1:3].encode()
        else:
            out += enc(part)
    if len(out) % 2:
        out += b" "
    for i in range(0, len(out), 2):
        if out[i] in b"0123456789" and not re.match(rb"[01][0-9A-Z]", out[i:i + 2]):
            die(f"training: a unit starts with a digit in {s!r}")
    return out


def build_training(hag, entries):
    """Repacks the training lines into the space the Japanese ones took and moves the pointers."""
    a, b = entries[TRAIN_ENTRY]
    e = bytearray(hag[a:b])
    addr = lambda o: TRAIN_BASE + o
    rows = {int(f[0], 16): f[2] for _, f in read_tsv(TRAINING, 3)}
    w32 = lambda o: struct.unpack_from("<I", e, o)[0]
    lines = []           # (pointer's offset, line offset)
    for p in range(TRAIN_NPAGES):
        pa = w32(TRAIN_PAGES - TRAIN_BASE + 4 * p)
        k = 0
        while pa:
            q = pa - TRAIN_BASE + 4 * k
            la = w32(q)
            if not la:
                break
            lines.append((q, la - TRAIN_BASE))
            k += 1
    offs = sorted({lo for _, lo in lines})
    if set(offs) != set(rows):
        die(f"training.tsv: lines {sorted(set(offs) ^ set(rows))} differ from the disc's")
    lo = offs[0]
    end = offs[-1]
    while e[end]:
        end += 2
    hi = (end + 2 + 3) & ~3
    pool, at = bytearray(), {}
    for o in offs:
        at[o] = lo + len(pool)
        pool += train_units(rows[o]) + b"\0\0"
        pool += bytes(-len(pool) % 4)
    if len(pool) > hi - lo:
        die(f"training: the English takes {len(pool)} bytes, the room is {hi - lo}")
    e[lo:hi] = pool + bytes(hi - lo - len(pool))
    for q, o in lines:
        struct.pack_into("<I", e, q, addr(at[o]))
    hag[a:b] = e
    return len(pool), hi - lo


def build_ui(hag):
    """The heading and button pictures: each English PNG over the Japanese texels, where words.tsv's
    disc column says they are (tools/ui_words.py locate). Returns how many places were written."""
    from PIL import Image
    import ui_words
    done = {}
    for r in ui_words.read_rows():
        p = UI / "en" / f"{r['id']}.png"
        if r["english"] in ("", "-") or not p.exists():
            continue
        if not r.get("disc"):
            die(f"words.tsv: {r['id']} ({r['english']}) has no disc place (tools/ui_words.py locate)")
        w, h = int(r["w"]), int(r["h"])
        en = Image.open(p).tobytes()
        rows = [bytes(en[y * w + x] | (en[y * w + x + 1] << 4) for x in range(0, w, 2)) for y in range(h)]
        for place in r["disc"].split(","):
            off, stride = (int(v, 16) for v in place.split("/"))
            if (off, stride) in done:          # one picture drawn in two palettes (オン, オフ)
                if done[off, stride] != rows:
                    die(f"words.tsv: {r['id']} shares its texels with another word but not its English")
                continue
            px = [v for y in range(h) for b in hag[off + y * stride:off + y * stride + w // 2] for v in (b & 15, b >> 4)]
            if ui_words.fnv(px) != int(r["hash"], 16):
                die(f"{r['id']}: the disc's picture at {off:#x} is not the Japanese one")
            for y, row in enumerate(rows):
                hag[off + y * stride:off + y * stride + len(row)] = row
            done[off, stride] = rows
    return len(done)


# The big headings (ポーズ on the pause screen, コンティニュー？ イエス ノー on the continue screen) are
# sprites from a 48 px katakana font (HAGECHO entry 151, 4bpp, white = index 15), placed by tables of
# 12-byte entries {s8 sx, s8 sy, attr, depth, s16 x, s16 y, frame, r, g, b} (centres; sx 16 = full
# size) that f_80048ee4 draws. The frames only these headings use become Latin letters.
#
# The banners スタート！ (a match's start) and クリアー！ (a stage cleared) use the same font through
# f_80042584: lists of 8-byte entries {s16 x, s16 y, s16 0, s16 frame} (centres, full size, a zero
# frame ends the list), read by a task f_80042b70 starts. Their eight frames ス タ ー ト ！ ク リ ア
# are theirs alone, and become S T E L ! C R A in letters a little bigger; the lists, six entries
# now, move to the old jump table's space.
BIG_ENTRY = 151
BIG_FRAMES = {   # frame: (offset in entry 151, box size), the glyph it had
    0x90: (0x11964, 56),  # ポ
    0x88: (0xF224, 56),   # ズ
    0x85: (0xE4A4, 48),   # コ
    0x94: (0x12D04, 48),  # ン
    0x8C: (0x10764, 48),  # テ
    0x80: (0xCE24, 48),   # ィ
    0x8E: (0x11064, 48),  # ニ
    0x91: (0x11F84, 48),  # ュ
    0x8F: (0x114E4, 48),  # ノ
    0x81: (0xD2A4, 48),   # イ
    0x83: (0xDBA4, 48),   # エ
    0x7E: (0xBC24, 48),   # ？
    0x87: (0xEDA4, 48),   # ス
    0x8A: (0xFE64, 48),   # タ
    0x95: (0xC524, 48),   # ー
    0x8D: (0x10BE4, 48),  # ト
    0x7D: (0xC0A4, 48),   # ！
    0x84: (0xE024, 48),   # ク
    0x93: (0x12884, 48),  # リ
    0x7F: (0xC9A4, 48),   # ア
}
BIG_LETTERS = {"P": 0x90, "A": 0x88, "U": 0x85, "S": 0x94, "E": 0x8C, "C": 0x80, "O": 0x8E, "N": 0x91,
               "T": 0x8F, "I": 0x81, "Y": 0x83, "?": 0x7E}
BIG_TABLES = [   # (heading, table's address, where to put it, code that loads the address (lui, addiu),
                 #  centre x, y, sx, scale for spacing)
    ("PAUSE", 0x800A483C, TABLES + 304, (0x80040AD0, 0x80040AD4), 2, -4, 12),
    ("CONTINUE?", 0x800A61C4, TABLES + 376, (0x80045F9C, 0x80045FA0), 0, -24, 16),
    ("YES", 0x800A6234, None, None, -57, 40, 16),
    ("NO", 0x800A6264, None, None, 68, 40, 16),
]
BIG_HEIGHT, BIG_GAP = 36, 3
BANNER_LETTERS = {"S": 0x87, "T": 0x8A, "E": 0x95, "L": 0x8D, "!": 0x7D, "C": 0x84, "R": 0x93, "A": 0x7F}
BANNERS = [   # (word, list's address, its frames, where to put it, code that loads the address (lui, addiu),
              #  centre x: the middle of the Japanese)
    ("START!", 0x800A4E5C, (0x87, 0x8A, 0x95, 0x8D, 0x7D), TABLES + 496, (0x80042BBC, 0x80042BC4), 6),
    ("CLEAR!", 0x800A4E8C, (0x84, 0x93, 0x7F, 0x95, 0x7D), TABLES + 552, (0x80042BE0, 0x80042BE8), 1),
]
BANNER_HEIGHT = 40


def build_big(ara, hag, entries):
    """The big headings in English: letters into the frames, then the tables."""
    import ui_lettering
    at = lambda addr: IMAGE + addr - BASE
    base = entries[BIG_ENTRY][0]
    def repoint(old, new, code):
        lui, addiu = code
        hi, lo = (old + 0x8000) >> 16, old & 0xFFFF
        if struct.unpack_from("<I", ara, at(lui))[0] != 0x3C040000 | hi or \
                struct.unpack_from("<I", ara, at(addiu))[0] != 0x24840000 | lo:
            die(f"the code at {lui:#x}, {addiu:#x} does not load {old:#x}")
        hi, lo = (new + 0x8000) >> 16, new & 0xFFFF
        ara[at(lui):at(lui) + 4] = struct.pack("<I", 0x3C040000 | hi)        # lui a0, hi
        ara[at(addiu):at(addiu) + 4] = struct.pack("<I", 0x24840000 | lo)    # addiu a0, a0, lo

    widths, bwidths = {}, {}
    for ch, f, height, ws in [(c, f, BIG_HEIGHT, widths) for c, f in BIG_LETTERS.items()] + \
                             [(c, f, BANNER_HEIGHT, bwidths) for c, f in BANNER_LETTERS.items()]:
        off, box = BIG_FRAMES[f]
        g = ui_lettering.big_glyph(ch, height)
        h, w = len(g), len(g[0])
        if w > box or h > box:
            die(f"big {ch}: {w}x{h} does not fit its {box} px frame")
        x0, y0 = (box - w) // 2, (box - h) // 2
        px = bytearray(box * box)
        for y, row in enumerate(g):
            for x, c in enumerate(row):
                if c == "#":
                    px[(y0 + y) * box + x0 + x] = 15
        o = base + off
        hag[o:o + box * box // 2] = bytes(px[i] | px[i + 1] << 4 for i in range(0, len(px), 2))
        ws[ch] = w
    for word, addr, new, code, cx, cy, sx in BIG_TABLES:
        o = at(addr)
        old = []
        while struct.unpack_from("<H", ara, o + 12 * len(old))[0]:
            old.append(bytes(ara[o + 12 * len(old):o + 12 * len(old) + 12]))
        attr, depth, rgb = old[0][2], old[0][3], old[0][9:12]
        ws = [widths[c] * sx / 16 for c in word]
        total = sum(ws) + BIG_GAP * sx / 16 * (len(word) - 1)
        x, out = cx - total / 2, b""
        for c, w in zip(word, ws):
            out += struct.pack("<bbBBhhB", sx, sx, attr, depth, round(x + w / 2), cy, BIG_LETTERS[c]) + rgb
            x += w + BIG_GAP * sx / 16
        out += bytes(12)
        if new is None:
            if len(out) > 12 * (len(old) + 1):
                die(f"big {word}: {len(word)} letters, the table holds {len(old)}")
            ara[o:o + len(out)] = out
        else:
            ara[at(new):at(new) + len(out)] = out
            repoint(addr, new, code)
    for word, addr, was, new, code, cx in BANNERS:
        if tuple(struct.unpack_from("<h", ara, at(addr) + 8 * i + 6)[0] for i in range(6)) != was + (0,):
            die(f"banner {word}: the list at {addr:#x} is not the one expected")
        ws = [bwidths[c] for c in word]
        x, out = cx - (sum(ws) + BIG_GAP * (len(word) - 1)) / 2, b""
        for c, w in zip(word, ws):
            out += struct.pack("<hhhh", round(x + w / 2), 0, 0, BANNER_LETTERS[c])
            x += w + BIG_GAP
        out += bytes(8)
        ara[at(new):at(new) + len(out)] = out
        repoint(addr, new, code)
    return [w for w, *_ in BIG_TABLES] + [w for w, *_ in BANNERS]


def hagecho_entries(do):
    offs = struct.unpack(f"<{len(do) // 4}I", do)
    return [(offs[i], offs[i + 1]) for i in range(len(offs) - 1)]


def patch(files, report=False):
    """files: {name: bytearray}; patched in place. Returns a summary."""
    ara, hag = files["ARA.BIN"], files["HAGECHO.BIN"]
    entries = hagecho_entries(bytes(files["DO.BIN"]))
    at = lambda addr: IMAGE + addr - BASE
    # the font: half-width glyphs into the hiragana rows of the sheet (entry 0)
    s0 = entries[0][0] + SHEET
    sheet, widths = halfwidth.build(bytes(hag[s0:s0 + 256 * 128]), HALF_ROW)
    hag[s0:s0 + 256 * 128] = sheet
    adv = bytes((w + 1) if w else 4 for w in widths)
    # tables in the old jump table's space: the advances, and the punctuation cells it encoded
    punct = bytearray()
    for i in range(180):
        t = struct.unpack_from("<I", ara, at(TABLES + 4 * i))[0]
        i0, i1 = struct.unpack_from("<II", ara, at(t))
        if i0 != 0x03E00008 or i1 >> 16 != 0x2402:
            die(f"punctuation table entry {i}: unexpected code at {t:#x}")
        punct.append(i1 & 0xFF)
    ara[at(ADV):at(ADV) + 96] = adv
    ara[at(PUNCT):at(PUNCT) + 180] = punct
    rng = b"".join(struct.pack("<HBB", lo - 0x8000, n, c) for lo, n, c in MAP_RANGES)
    ara[at(PUNCT) + 180:at(TABLES) + 720] = rng + bytes(720 - 276 - len(rng))
    # the code
    syms = dict(F_QUAD=F_QUAD, COLOURS=COLOURS, ADV=ADV, PUNCT=PUNCT, RANGES=RANGES, HALF_CELL0=HALF_ROW * 16)
    block, lb = assemble(ASM / "block.s", BLOCK, syms)
    if len(block) > BLOCK_END - BLOCK or lb["mapper"] != BLOCK or lb["print"] != 0x80043348:
        die(f"block.s: {len(block)} bytes, mapper {lb['mapper']:#x}, print {lb['print']:#x}")
    glyph, lg = assemble(ASM / "glyph.s", GLYPH, dict(syms, MAPPER=lb["mapper"], FIXQUAD=lb["fixquad"]))
    if len(glyph) > GLYPH_END - GLYPH:
        die(f"glyph.s: {len(glyph)} bytes, the room is {GLYPH_END - GLYPH}")
    ara[at(BLOCK):at(BLOCK_END)] = block + bytes(BLOCK_END - BLOCK - len(block))
    ara[at(GLYPH):at(GLYPH_END)] = glyph + bytes(GLYPH_END - GLYPH - len(glyph))
    probs = build_strings(files, adv, report)
    tn, troom = build_training(hag, entries)
    nui = build_ui(hag)
    big = build_big(ara, hag, entries)
    return dict(big=big, block=len(block), glyph=len(glyph), training=(tn, troom), ui=nui, problems=probs)


# ---- main --------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inp", metavar="IN")
    ap.add_argument("out", metavar="OUT")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    inp, out = Path(a.inp), Path(a.out)
    ext = inp.suffix.lower()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        extra = []                 # other tracks' files to carry over: (src, name)
        if ext == ".chd":
            if not shutil.which("chdman"):
                die("chdman not found (MAME tools)")
            subprocess.run(["chdman", "extractcd", "-i", str(inp), "-o", str(td / "d.cue"), "-ob", str(td / "d.bin")],
                           check=True, capture_output=True)
            track_path, cue = td / "d.bin", td / "d.cue"
        elif ext == ".cue":
            fl = parse_cue(inp)
            if not fl:
                die(f"{inp}: no FILE in the cue sheet")
            track_path, cue = inp.parent / fl[0][0], inp
            extra = [(inp.parent / f[0], f[0]) for f in fl[1:]]
        elif ext in (".bin", ".img", ".iso"):
            track_path, cue = inp, None
        else:
            die(f"{inp}: give a .chd, .cue, .bin or .iso")
        t = Track(track_path)
        check_ecc(t)
        for name in ("ARA.BIN", "HAGECHO.BIN", "DO.BIN", "SLPM_862.72"):
            if name not in t.files:
                die(f"no {name}: not Rakugaki Showtime (SLPM-86272)?")
        files = {n: bytearray(t.read(n)) for n in ("ARA.BIN", "HAGECHO.BIN", "DO.BIN")}
        for n, want in KNOWN.items():
            got = hashlib.sha1(files[n]).hexdigest()
            if want and got != want:
                die(f"{n}: not the Japanese release's (sha1 {got})")
        res = patch(files, a.report)
        for p in res["problems"]:
            print("  " + p, file=sys.stderr)
        if res["problems"]:
            die(f"{len(res['problems'])} problems; nothing written")
        for n in ("ARA.BIN", "HAGECHO.BIN"):
            t.write(n, bytes(files[n]))
        out.parent.mkdir(parents=True, exist_ok=True)
        if ext == ".chd":
            t.save(td / "d.bin")
            o = out.with_suffix(".chd")
            subprocess.run(["chdman", "createcd", "-f", "-i", str(cue), "-o", str(o)], check=True, capture_output=True)
        elif ext == ".cue":
            stem = out.with_suffix("")
            names = [f"{stem.name} (Track {i + 1:02d}).bin" if extra else f"{stem.name}.bin" for i in range(1 + len(extra))]
            t.save(stem.parent / names[0])
            for (src, _), nm in zip(extra, names[1:]):
                shutil.copyfile(src, stem.parent / nm)
            text = Path(cue).read_text(errors="replace")
            for (_, old), nm in zip([(None, parse_cue(cue)[0][0])] + extra, names):
                text = text.replace(f'"{old}"', f'"{nm}"', 1)
            o = stem.with_suffix(".cue")
            o.write_text(text)
        else:
            o = out.with_suffix(ext)
            t.save(o)
    print(f"{o}: code {res['block']} + {res['glyph']} bytes, training {res['training'][0]}/{res['training'][1]} bytes, "
          f"{res['ui']} pictures, big headings {' '.join(res['big'])}, {len(t.dirty)} sectors changed")


if __name__ == "__main__":
    main()
