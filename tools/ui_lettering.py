"""The game's English lettering, as a 16 px alphabet for the UI word pictures (tools/ui_words.py draft).

The game itself draws "PRESS SELECT + START TO EXIT" (character select) in an 8 px lettering that
matches its katakana headings: each letter's top half is a solid rounded blob, the bottom half 2 px
strokes, and the whole letter leans right (rows shifted 2,2,2,2,1,1,0,0 px). Ten of its letters
(A C E I L O P R S X) are kept here as drawn; the rest of A-Z, the digits and some punctuation are
drawn upright in the same scheme and given the lean. T and D are redrawn: squeezed, the game's T read
as a 7 and a D like the game's would close into a B.

Words in 8 px slots use the letters as they are (glyphs8). A 16 px heading is made from them as follows:
- each letter is doubled to 16 px with EPX (Scale2x), which rounds the diagonals as the katakana are;
- the letters are squeezed by merging adjacent columns, cheapest first, so counters stay open;
- the word is set with row-by-row kerning, so the slanted letters interlock with `gap` clear pixels.
"""

H = 16                                   # letter height after EPX
SHIFT = [2, 2, 2, 2, 1, 1, 0, 0]         # the game's lean, per 8 px row

# The game's own letters, exactly as drawn (already leaning).
GAME = {
    "A": ["...#####.", "..#######", "..#######", "..#######", ".##...##.", ".#######.", "##...##..", "##...##.."],
    "C": ["...####.", "..######", "..######", ".######.", ".##.....", "##......", "##......", ".####..."],
    "E": ["...####.", "..######", "..######", "..#####.", ".##.....", ".####...", "##......", "#####..."],
    "I": ["...##.", "..####", "..####", ".####.", ".####.", "####..", "####..", ".##..."],
    "L": ["..##..", "..##..", ".##...", ".##...", ".#####", "######", "######", "#####."],
    "O": ["...#####.", "..#######", "..#######", "..######.", ".##...##.", ".##..##..", "##...##..", ".#####..."],
    "P": ["...####.", "..######", "..######", "..######", ".##..##.", ".#####..", "##......", "##......"],
    "R": ["...####.", "..######", "..######", "..######", ".##..##.", ".####...", "##..##..", "##..##.."],
    "S": ["...####.", "..######", ".#######", ".######.", ".##.....", "..###...", "...###..", "#####..."],
    "X": ["...##..##", "..###.##.", "..#####..", "..####...", "...####..", "..#####..", ".##.###..", "##..##..."],
}
# Drawn to match, upright (the lean is added below).
NEW = {
    "B": ["#####.", "######", "######", "######", "##..##", "#####.", "##..##", "#####."],
    "D": ["####..", "#####.", "######", "######", "##..##", "##..##", "##..##", "#####."],
    "F": [".####.", "######", "######", "#####.", "##....", "####..", "##....", "##...."],
    "G": [".####.", "######", "######", "######", "##....", "##.###", "##..##", ".####."],
    "H": ["##..##", "##..##", "######", "######", "######", "##..##", "##..##", "##..##"],
    "J": ["..####", ".#####", ".#####", ".#####", "...##.", "...##.", "##.##.", ".###.."],
    "K": ["##..##", "##.###", "#####.", "####..", "####..", "##.##.", "##..##", "##..##"],
    "M": ["##...##", "###.###", "#######", "#######", "##.#.##", "##...##", "##...##", "##...##"],
    "N": ["##..##", "###.##", "######", "######", "##.###", "##..##", "##..##", "##..##"],
    "Q": [".#####.", "#######", "#######", "######.", "##...##", "##..##.", "##.###.", ".######"],
    "T": [".######.", "########", "########", ".######.", "...##...", "...##...", "...##...", "...##..."],
    "U": ["##..##", "##..##", "##..##", "##..##", "##..##", "######", "######", ".####."],
    "V": ["##..##", "##..##", "##..##", "##..##", "##..##", ".####.", ".####.", "..##.."],
    "W": ["##...##", "##...##", "##...##", "##...##", "##.#.##", "#######", "###.###", ".#...#."],
    "Y": ["##..##", "##..##", "######", "######", ".####.", "..##..", "..##..", "..##.."],
    "Z": [".#####", "######", "######", "######", "..##..", ".##...", "##....", "######"],
    "0": [".####.", "######", "######", "######", "##..##", "##..##", "##..##", ".####."],
    "1": [".##.", "###.", "###.", "###.", ".##.", ".##.", ".##.", "####"],
    "2": [".####.", "######", "######", "######", "...##.", "..##..", ".##...", "######"],
    "3": ["#####.", "######", "######", "######", "...##.", ".####.", "....##", "#####."],
    "4": ["...##.", "..###.", ".####.", "##.##.", "######", "######", "...##.", "...##."],
    "5": ["######", "######", "#####.", "######", "....##", "....##", "##..##", ".####."],
    "6": [".####.", "######", "######", "######", "#####.", "##..##", "##..##", ".####."],
    "7": ["######", "######", "######", "######", "...##.", "..##..", ".##...", ".##..."],
    "8": [".####.", "######", "######", "######", ".####.", "##..##", "##..##", ".####."],
    "9": [".####.", "######", "######", "######", "##..##", ".#####", "....##", ".####."],
    "?": [".####.", "######", "######", "######", "...##.", "..##..", "......", "..##.."],
    "!": [".##.", "####", "####", "####", ".##.", ".##.", "....", ".##."],
    "-": ["....", "....", "....", "....", "####", "####", "....", "...."],
    ".": ["..", "..", "..", "..", "..", "..", "##", "##"],
    "'": ["##", "##", "##", "..", "..", "..", "..", ".."],
    "+": ["......", "......", "..##..", "######", "######", "..##..", "......", "......"],
    "/": ["....##", "....##", "...##.", "...##.", "..##..", "..##..", ".##...", ".##..."],
    ":": ["..", "##", "##", "..", "..", "##", "##", ".."],
}
ORDER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789?!-.'+/:"


def _lean(rows):
    w = max(len(r) for r in rows) + 2
    return [("." * SHIFT[i] + r).ljust(w, ".") for i, r in enumerate(rows)]


def _trim(rows):
    cols = [x for x in range(max(map(len, rows))) if any(x < len(r) and r[x] == "#" for r in rows)]
    return [r.ljust(cols[-1] + 1, ".")[cols[0]:cols[-1] + 1] for r in rows]


def _epx(rows):
    """Scale2x: each pixel becomes 4, a corner taking its two neighbours' colour where they agree."""
    h, w = len(rows), len(rows[0])
    g = lambda x, y: 0 <= x < w and 0 <= y < h and rows[y][x] == "#"
    out = [[False] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        for x in range(w):
            P, A, B, C, D = g(x, y), g(x, y - 1), g(x + 1, y), g(x - 1, y), g(x, y + 1)
            o = [P] * 4
            if C == A and C != D and A != B: o[0] = A
            if A == B and A != C and B != D: o[1] = B
            if D == C and D != B and C != A: o[2] = C
            if B == D and B != A and D != C: o[3] = D
            out[2 * y][2 * x], out[2 * y][2 * x + 1], out[2 * y + 1][2 * x], out[2 * y + 1][2 * x + 1] = o
    return ["".join("#" if c else "." for c in r) for r in out]


def _squeeze(rows, target):
    """Merges adjacent columns (OR) until `target` wide, the cheapest pair first. A pair costs the pixels
    that differ between them, plus 6 for each 1 px gap the merge would close, which keeps counters open."""
    cols = ["".join(r[x] for r in rows) for x in range(len(rows[0]))]
    blank = "." * len(rows)
    while len(cols) > target:
        best = None
        for i in range(len(cols) - 1):
            a, b = cols[i], cols[i + 1]
            L = cols[i - 1] if i > 0 else blank
            R = cols[i + 2] if i + 2 < len(cols) else blank
            cost = sum(p != q for p, q in zip(a, b))
            cost += 6 * sum((a[y] == "." and b[y] == "#" and L[y] == "#") or (b[y] == "." and a[y] == "#" and R[y] == "#")
                            for y in range(len(a)))
            if best is None or cost < best[0]:
                best = (cost, i)
        i = best[1]
        cols[i:i + 2] = ["".join("#" if "#" in pq else "." for pq in zip(cols[i], cols[i + 1]))]
    return ["".join(c[y] for c in cols) for y in range(len(cols[0]))]


def glyphs(squeeze=1.0):
    """The 16 px alphabet (rows of '#' and '.'), each letter squeezed to `squeeze` of its width."""
    g8 = dict(GAME)
    g8.update({k: _lean(v) for k, v in NEW.items()})
    out = {}
    for k, v in g8.items():
        r = _epx(_trim(v))
        out[k] = _squeeze(r, max(2, round(len(r[0]) * squeeze))) if squeeze < 1 else r
    return out


def glyphs8():
    """The 8 px alphabet as the game draws it (leaned, no doubling), for words in 8 px slots."""
    g8 = dict(GAME)
    g8.update({k: _lean(v) for k, v in NEW.items()})
    return {k: _trim(v) for k, v in g8.items()}


def _edge(rows, last):
    out = []
    for r in rows:
        xs = [x for x, c in enumerate(r) if c == "#"]
        out.append((xs[-1] if last else xs[0]) if xs else None)
    return out


def setword(text, g, gap=1, space=5):
    """The text as rows of '#'/'.', as tall as the glyphs in g (H, or 8 for glyphs8). Each letter goes as far left as its rows allow, with `gap`
    clear pixels to the ink before it in the same row and the rows either side (so strokes never touch
    corner to corner); a space starts afresh `space` px after the last ink. Unknown characters are skipped."""
    H = len(next(iter(g.values())))
    right = [None] * H
    pen, placed = 0, []
    for c in text.upper():
        if c == " ":
            ink = [r for r in right if r is not None]
            pen = (max(ink) + 1 if ink else pen) + space
            right = [None] * H
            continue
        if c not in g:
            continue
        rows = g[c]
        lp = _edge(rows, False)
        x = None
        for y in range(H):
            if lp[y] is None:
                continue
            for yy in (y - 1, y, y + 1):
                if 0 <= yy < H and right[yy] is not None:
                    want = right[yy] + gap + 1 - lp[y]
                    x = want if x is None else max(x, want)
        x = pen if x is None else max(x, pen - 2 if pen else 0)
        placed.append((x, rows))
        for y, e in enumerate(_edge(rows, True)):
            if e is not None:
                right[y] = x + e if right[y] is None else max(right[y], x + e)
        pen = x + len(rows[0])
    if not placed:
        return ["."] * H
    x0 = min(x for x, _ in placed)
    out = [["."] * (max(x + len(r[0]) for x, r in placed) - x0) for _ in range(H)]
    for x, rows in placed:
        for y, r in enumerate(rows):
            for xx, ch in enumerate(r):
                if ch == "#":
                    out[y][x - x0 + xx] = "#"
    return ["".join(r) for r in out]


# Big letters drawn differently: the 8 px T's stem, under the left of its bar once leaned, reads as a
# 7 at this size; here it sits under the bar's middle.
BIG_NEW = {"T": [".######.", "########", "########", ".######.", "....##..", "....##..", "....##..", "....##.."]}


def big_glyph(ch, height=36, squeeze=0.8):
    """One letter for the game's big headings (the 48 px sprite font of ポーズ, コンティニュー？):
    the 8 px letter doubled three times with EPX, rounded off and scaled to `height` px, `squeeze`
    of its width. Returns rows of '#'/'.' cropped to the ink."""
    from PIL import Image, ImageFilter
    g8 = dict(GAME)
    g8.update({k: _lean(v) for k, v in {**NEW, **BIG_NEW}.items()})
    r = _trim(g8[ch])
    for _ in range(3):
        r = _epx(r)
    im = Image.new("L", (len(r[0]), len(r)))
    im.putdata([255 if c == "#" else 0 for row in r for c in row])
    im = im.filter(ImageFilter.GaussianBlur(3)).point(lambda p: 255 if p > 110 else 0)
    w = max(1, round(im.width * height / im.height * squeeze))
    im = im.resize((w, height), Image.LANCZOS).point(lambda p: 255 if p > 128 else 0)
    im = im.crop(im.getbbox())
    px = im.tobytes()
    return ["".join("#" if px[y * im.width + x] else "." for x in range(im.width)) for y in range(im.height)]
