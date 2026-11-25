# English text for the original disc: the game's f_8003ce18, rewritten in its place (0x8003ce18,
# 76 instructions at most). It draws one 16 px text unit on a free quad (corners given, so it can
# turn and scale): the training text uses it for every 2-byte unit of a line, the units centred.
# An SJIS unit is the game's 16 px glyph as before; a unit whose first byte is below 0x80 is two
# half-width glyphs (ASCII 0x20..0x7f), one in each half of the quad, so English gets 8 px a letter
# and the game's centring still holds. A space draws nothing.
#
#   a0 corners (4 x/y pairs, 8 bytes apart), a1 r, a2 g, a3 b,
#   16(sp) semi-transparent flag (byte), 20(sp) OT slot, 24(sp) the unit's 2 bytes

        .set    noreorder
        .set    noat
        .text

glyph:
        addiu   $sp, $sp, -48
        sw      $ra, 44($sp)
        sw      $s4, 40($sp)
        sw      $s3, 36($sp)
        sw      $s2, 32($sp)
        sw      $s1, 28($sp)
        sw      $s0, 24($sp)
        move    $s0, $a0
        andi    $a1, $a1, 0xff
        andi    $a2, $a2, 0xff
        sll     $a2, $a2, 8
        or      $a1, $a1, $a2
        andi    $a3, $a3, 0xff
        sll     $a3, $a3, 16
        or      $s1, $a1, $a3           # rgb
        lbu     $s4, 64($sp)            # semi-transparent
        lw      $s2, 72($sp)            # the unit
        lw      $t0, 68($sp)
        nop
        sw      $t0, 16($sp)            # the slot, for F_QUAD
        lbu     $t0, 0($s2)
        lbu     $t1, 1($s2)
        sltiu   $t2, $t0, 0x80
        bne     $t2, $zero, g_ascii
        sll     $a0, $t0, 8
        jal     MAPPER
        or      $a0, $a0, $t1
        addiu   $t0, $zero, 255
        beq     $v0, $t0, g_ret
        addiu   $s3, $zero, 2           # side 2: the whole quad
        b       g_draw
        move    $a0, $v0
g_ascii:
        move    $s3, $zero              # side 0, then 1
g_side:
        addu    $t0, $s2, $s3
        lbu     $t0, 0($t0)
        nop
        addiu   $t0, $t0, -0x20
        blez    $t0, g_next             # a space (or padding) draws nothing
        sw      $t0, 20($sp)
        srl     $a0, $t0, 1
        addiu   $a0, $a0, HALF_CELL0
g_draw:
        move    $a1, $zero
        move    $a2, $zero
        jal     F_QUAD
        move    $a3, $s1
        beq     $v0, $zero, g_next
        move    $a0, $v0
        move    $a1, $s0
        move    $a2, $s3
        slti    $t0, $s3, 2
        beq     $t0, $zero, g_fix
        addiu   $a3, $zero, -1          # the whole cell
        lw      $a3, 20($sp)            # a half-width side: its glyph
        nop
g_fix:
        jal     FIXQUAD
        nop
        beq     $s4, $zero, g_next
        nop
        lbu     $t0, 7($a0)
        nop
        ori     $t0, $t0, 2
        sb      $t0, 7($a0)
g_next:
        addiu   $s3, $s3, 1
        slti    $t0, $s3, 2
        bne     $t0, $zero, g_side
        nop
g_ret:
        lw      $ra, 44($sp)
        lw      $s4, 40($sp)
        lw      $s3, 36($sp)
        lw      $s2, 32($sp)
        lw      $s1, 28($sp)
        lw      $s0, 24($sp)
        jr      $ra
        addiu   $sp, $sp, 48
glyph_end:
