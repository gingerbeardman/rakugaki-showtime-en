"""The 8 px half-width font for the disc patch (tools/en_disc.py), made from the game's own 16x16
font sheet.

The sheet (VRAM 960,256; 4bpp, 256x256 texels, 128 bytes a row) holds four 1-bit fonts, one per
bitplane: four hand-drawn "scribble" frames of every glyph, which the game cycles so text wobbles. Each
Latin, digit and symbol glyph is cut to its width over all four frames and, if wider than 7 px, squeezed
by merging neighbouring columns. The ones the game lacks are drawn here.
"""

# Glyphs the game lacks, the same in all four frames: 16 rows of up to 8 columns, '#' set.
DRAWN = {
    "(": ["", "", "....#", "...#", "..#", "..#", "..#", "..#", "..#", "..#", "..#", "..#", "...#", "....#"],
    ")": ["", "", "..#", "...#", "....#", "....#", "....#", "....#", "....#", "....#", "....#", "....#", "...#", "..#"],
    "*": ["", "", "", "", "", "...#", ".#.#.#", "..###", ".#.#.#", "...#"],
    ",": ["", "", "", "", "", "", "", "", "", "", "", "...##", "...##", "....#", "...#"],
    "-": ["", "", "", "", "", "", "", "", ".####"],
    ".": ["", "", "", "", "", "", "", "", "", "", "", "", "...##", "...##"],
    "@": ["", "", "", "", "..###", ".#...#", "#..##.#", "#.#.#.#", "#.#.#.#", "#..###", ".#", "..####"],
    "[": ["", "", "..###", "..#", "..#", "..#", "..#", "..#", "..#", "..#", "..#", "..#", "..#", "..###"],
    "\\": ["", "", ".#", ".#", "..#", "..#", "..#", "...#", "...#", "....#", "....#", "....#", ".....#", ".....#"],
    "]": ["", "", "..###", "....#", "....#", "....#", "....#", "....#", "....#", "....#", "....#", "....#", "....#", "..###"],
    "^": ["", "", "...#", "..#.#", ".#...#"],
    "_": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "#######"],
    "`": ["", "", "..#", "...#"],
    "{": ["", "", "....##", "...#", "...#", "...#", "...#", ".##", "...#", "...#", "...#", "...#", "...#", "....##"],
    "|": ["", "", "...#", "...#", "...#", "...#", "...#", "...#", "...#", "...#", "...#", "...#", "...#", "...#"],
    "}": ["", "", ".##", "...#", "...#", "...#", "...#", "....##", "...#", "...#", "...#", "...#", "...#", ".##"],
}
_SYM = "!\"#$%&'+/:;<=>?~"
_SYM_CELL = [0xfc, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x2b, 0xf8, 0xf6, 0xf7, 0x4e, 0x2f, 0x4f, 0xfb, 0xfe]


def source_cell(c):
    """The full-width sheet cell a half-width glyph is made from, or None."""
    if "0" <= c <= "9": return ord(c) - 48
    if "A" <= c <= "Z": return 17 + ord(c) - 65
    if "a" <= c <= "z": return 49 + ord(c) - 97
    if c and c in _SYM: return _SYM_CELL[_SYM.index(c)]
    return None


def _nib(sheet, u, v):
    return (sheet[v * 128 + u // 2] >> ((u & 1) * 4)) & 15


def _squeeze(col):
    """Merge (OR) neighbouring columns, cheapest pair first, until at most 7 wide; a pair costs the
    pixels in which the two differ plus 10 for each 1 px gap between strokes it would close."""
    pc = lambda v: bin(v).count("1")
    col = list(col)
    while len(col) > 7:
        best, bc = 0, 1 << 30
        for c in range(len(col) - 1):
            l = col[c - 1] if c > 0 else 0
            a, b = col[c], col[c + 1]
            r = col[c + 2] if c + 2 < len(col) else 0
            cost = pc(a ^ b) + 10 * pc((l & ~a & b) | (a & ~b & r))
            if cost < bc:
                bc, best = cost, c
        col[best:best + 2] = [col[best] | col[best + 1]]
    return col


def glyph(sheet, c):
    """ASCII c as up to 7 columns (bit row*4+plane: all four frames), left-aligned."""
    cell = source_cell(c)
    col = [0] * 16
    if cell is None:
        for r, row in enumerate(DRAWN.get(c, [])):
            for t, ch in enumerate(row[:8]):
                if ch == "#":
                    col[t] |= 15 << (r * 4)
    else:
        u0, v0 = (cell & 15) * 16, cell & 0xF0
        for t in range(16):
            for r in range(16):
                col[t] |= _nib(sheet, u0 + t, v0 + r) << (r * 4)
    ink = [i for i, v in enumerate(col) if v]
    if not ink:
        return []
    return _squeeze(col[ink[0]:ink[-1] + 1])


def build(sheet, row0):
    """The 96 half-width glyphs (ASCII 0x20..0x7f, two to a 16 px cell) written over sheet rows
    row0..row0+2 (cell rows, 16 px each): returns (the new sheet, widths[96])."""
    sheet = bytearray(sheet)
    made = [glyph(bytes(sheet), chr(0x20 + s)) for s in range(96)]   # all first: the rows get overwritten
    for s, col in enumerate(made):
        u, v = (s & 31) * 8, (row0 + s // 32) * 16
        for r in range(16):
            for x in range(8):
                n = (col[x] >> (r * 4)) & 15 if x < len(col) else 0
                i = (v + r) * 128 + (u + x) // 2
                sh = ((u + x) & 1) * 4
                sheet[i] = (sheet[i] & ~(15 << sh) & 0xFF) | (n << sh)
    return bytes(sheet), [len(c) for c in made]
