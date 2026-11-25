# English text for the original disc: the code that replaces the game's printer chain at
# 0x800430dc..0x800433d0 (assembled by tools/en_disc.py; MIPS I, no reorder: every load's next
# instruction leaves the loaded register alone, and branch delay slots are filled by hand).
#
#   0x800430dc  mapper(code)        SJIS code -> font sheet cell, or 255: the game's f_800430dc, compact
#   ...         print_body          the printer
#   ...         fixquad             cuts a cell's quad to one half-width glyph
#   0x80043348  print(str, x, y, colour, [sp+16] slot)   the game's f_80043348, calls print_body
#   ...         half(s, x, y, rgb)  one half-width glyph (ASCII 0x20 + s) as a 7 px quad
#
# The half-width glyphs are ASCII 0x20..0x7f in font sheet cell rows 5..7 (two 8 px glyphs a cell,
# where the hiragana were). Strings: a byte from 0x20 to 0x7f is a half-width glyph advancing by
# ADV[c - 0x20] px; 0x01 n moves the pen n - 128 px right (alignment, worked out by the patcher);
# 0x09 moves to the next 16 px column from the string's start; other bytes below 0x20 are
# padding (nothing); from 0x80 an SJIS pair, a 16 px glyph from the game's font as before.
#
# The symbols in capitals are set by tools/en_disc.py: F_QUAD (the game's f_80042f28, which adds a
# 16x16 font POLY_FT4 to the OT and returns it), COLOURS, ADV, PUNCT and RANGES (tables in the old
# jump table's space), HALF_CELL0 (the first cell of the half-width glyphs).

        .set    noreorder
        .set    noat
        .text

# ---- mapper: a0 = SJIS code -> v0 = cell, 255 if none ------------------------------------------
mapper:
        addiu   $t2, $a0, -0x8000
        lui     $t3, %hi(RANGES)
        addiu   $t3, $t3, %lo(RANGES)
m_loop:                                 # RANGES: lo - 0x8000 (16 bits), count, first cell; count 0 ends
        lhu     $t0, 0($t3)
        lbu     $t1, 2($t3)
        lbu     $t4, 3($t3)
        subu    $t0, $t2, $t0
        beq     $t1, $zero, m_punct
        sltu    $t5, $t0, $t1
        beq     $t5, $zero, m_loop
        addiu   $t3, $t3, 4
        jr      $ra
        addu    $v0, $t0, $t4
m_punct:                                # the last entry's lo is 0x8141: punctuation by table
        sltiu   $t1, $t0, 180
        beq     $t1, $zero, m_ret
        addiu   $v0, $zero, 255
        lui     $t1, %hi(PUNCT)
        addu    $t1, $t1, $t0
        lbu     $v0, %lo(PUNCT)($t1)
m_ret:
        jr      $ra
        nop

# ---- print_body: a0 str, a1 x, a2 y, a3 colour index, 16(sp) OT slot -----------------------------
print_body:
        addiu   $sp, $sp, -56
        sw      $ra, 52($sp)
        sw      $s5, 48($sp)
        sw      $s4, 44($sp)
        sw      $s3, 40($sp)
        sw      $s2, 36($sp)
        sw      $s1, 32($sp)
        sw      $s0, 28($sp)
        lw      $t0, 72($sp)            # the slot, passed on at our 16(sp)
        move    $s0, $a0
        sw      $t0, 16($sp)
        move    $s1, $a1                # pen x
        move    $s2, $a2                # y
        move    $s4, $a1                # x the tab columns count from
        sll     $a3, $a3, 2
        lui     $t0, %hi(COLOURS)
        addu    $t0, $t0, $a3
        lw      $s3, %lo(COLOURS)($t0)  # rgb
p_loop:
        lbu     $t0, 0($s0)
        addiu   $s0, $s0, 1
        beq     $t0, $zero, p_done
        sltiu   $t1, $t0, 0x80
        beq     $t1, $zero, p_sjis
        sltiu   $t1, $t0, 0x20
        beq     $t1, $zero, p_glyph
        addiu   $t1, $zero, 1
        bne     $t0, $t1, p_notoff
        addiu   $t1, $zero, 9
        lbu     $t2, 0($s0)             # 0x01 n: pen n - 128 px right
        addiu   $s0, $s0, 1
        addu    $s1, $s1, $t2
        addiu   $s1, $s1, -128
        b       p_loop
        move    $s4, $s1
p_notoff:
        bne     $t0, $t1, p_loop        # padding
        subu    $t2, $s1, $s4
        sra     $t2, $t2, 4             # tab: the next 16 px column
        addiu   $t2, $t2, 1
        sll     $t2, $t2, 4
        b       p_loop
        addu    $s1, $s4, $t2
p_glyph:
        addiu   $s5, $t0, -0x20
        beq     $s5, $zero, p_adv       # a space draws nothing
        move    $a0, $s5
        move    $a1, $s1
        move    $a2, $s2
        jal     ABS_half
        move    $a3, $s3
        move    $a0, $s5                # the shadow: black, 1 px down and right
        addiu   $a1, $s1, 1
        addiu   $a2, $s2, 1
        jal     ABS_half
        move    $a3, $zero
p_adv:
        lui     $t0, %hi(ADV)
        addu    $t0, $t0, $s5
        lbu     $t0, %lo(ADV)($t0)
        b       p_loop
        addu    $s1, $s1, $t0
p_sjis:
        lbu     $t1, 0($s0)
        addiu   $s0, $s0, 1
        sll     $a0, $t0, 8
        jal     ABS_mapper
        or      $a0, $a0, $t1
        addiu   $t0, $zero, 255
        beq     $v0, $t0, p_adv16
        move    $s5, $v0
        move    $a0, $s5
        move    $a1, $s1
        move    $a2, $s2
        jal     F_QUAD
        move    $a3, $s3
        move    $a0, $s5
        addiu   $a1, $s1, 1
        addiu   $a2, $s2, 1
        jal     F_QUAD
        move    $a3, $zero
p_adv16:
        b       p_loop
        addiu   $s1, $s1, 16
p_done:
        lw      $ra, 52($sp)
        lw      $s5, 48($sp)
        lw      $s4, 44($sp)
        lw      $s3, 40($sp)
        lw      $s2, 36($sp)
        lw      $s1, 32($sp)
        lw      $s0, 28($sp)
        jr      $ra
        addiu   $sp, $sp, 56

# ---- fixquad: a0 prim, a1 corners (4 x/y pairs 8 bytes apart), a2 side, a3 glyph s or -1 ----------
# side 0: the quad from the corners' left edge over 7/16 of their width; side 1: the same from their
# middle; side 2: the corners as they are. s >= 0: the texture cut to its glyph's 8 px half (7 texels).
fixquad:
        bltz    $a3, fq_edges
        andi    $t0, $a3, 1
        sll     $t0, $t0, 3
        lbu     $t1, 12($a0)
        nop
        addu    $t1, $t1, $t0
        sb      $t1, 12($a0)
        sb      $t1, 28($a0)
        addiu   $t1, $t1, 7
        sb      $t1, 20($a0)
        sb      $t1, 36($a0)
fq_edges:
        move    $t9, $zero              # k = 0..3: x top, y top, x bottom, y bottom
fq_loop:
        andi    $t5, $t9, 1
        sll     $t5, $t5, 1
        srl     $t6, $t9, 1
        sll     $t6, $t6, 4
        addu    $t5, $t5, $t6           # the coordinate's offset in the corners
        addu    $t6, $a1, $t5
        lh      $t0, 0($t6)             # A: left corner
        lh      $t1, 8($t6)             # B: right corner
        move    $t2, $t0                # base = A
        subu    $t3, $t1, $t0           # d = B - A
        addiu   $t4, $zero, 2
        beq     $a2, $t4, fq_put
        sll     $t4, $t3, 3
        subu    $t3, $t4, $t3
        sra     $t3, $t3, 4             # d = (B - A) * 7 / 16
        beq     $a2, $zero, fq_put
        addu    $t4, $t0, $t1
        sra     $t2, $t4, 1             # side 1: base = the middle
fq_put:
        addu    $t3, $t2, $t3
        addu    $t6, $a0, $t5
        sh      $t2, 8($t6)
        sh      $t3, 16($t6)
        addiu   $t9, $t9, 1
        slti    $t4, $t9, 4
        bne     $t4, $zero, fq_loop
        nop
        jr      $ra
        nop

# ---- print: the game's entry point -------------------------------------------------------------
        .org    0x26c
print:
        addiu   $sp, $sp, -24
        sw      $ra, 20($sp)
        lw      $t0, 40($sp)
        nop
        jal     ABS_print_body
        sw      $t0, 16($sp)
        lw      $ra, 20($sp)
        nop
        jr      $ra
        addiu   $sp, $sp, 24

# ---- half: a0 s (glyph ASCII 0x20 + s), a1 x, a2 y, a3 rgb, 16(sp) slot ---------------------------
half:
        addiu   $sp, $sp, -32
        sw      $ra, 28($sp)
        sw      $s0, 24($sp)
        lw      $t0, 48($sp)
        move    $s0, $a0
        sw      $t0, 16($sp)
        srl     $a0, $a0, 1
        jal     F_QUAD
        addiu   $a0, $a0, HALF_CELL0
        beq     $v0, $zero, h_ret
        move    $a0, $v0
        addiu   $a1, $v0, 8             # its own corners
        move    $a2, $zero
        jal     ABS_fixquad
        move    $a3, $s0
h_ret:
        lw      $ra, 28($sp)
        lw      $s0, 24($sp)
        jr      $ra
        addiu   $sp, $sp, 32

block_end:
