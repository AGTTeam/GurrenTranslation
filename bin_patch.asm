.nds

strcmp     equ 0x02003d00
NFP2D      equ 0x0210c9b4
loadsprite equ 0x02013840

.open "data/repack/arm9.bin",0x02000000
;Replace wifi error codes
.org 0x021115e8
.area 0x46D
  CUSTOM_SPRITE:
  ;Return if != CUSTOM_SPRITE_05
  ldr r1,=CUSTOM_SPRITE_05
  add r0,r6,0x90
  bl strcmp
  cmp r0,0x0
  movne r0,0x1000
  addne r13,r13,0xc
  ;This should be "strhne r0,[r6,0x28]" but that doesn't seem to work in armips
  db 0xb8 :: db 0x02 :: db 0xc6 :: db 0x11
  popne r4-r7,r15
  ;Load sprite 2
  mvn r0,0x0
  str r0,[sp,0x0]
  add r4,r6,0xa8
  ldr r1,=NFP2D
  ldr r2,=CUSTOM_SPRITE_02
  add r0,r5,0x2c
  mov r3,0x0
  str r4,[sp,0x4]
  bl loadsprite
  ;Load sprite 3
  mvn r0,0x0
  str r0,[sp,0x0]
  add r4,r6,0xb0
  ldr r1,=NFP2D
  ldr r2,=CUSTOM_SPRITE_03
  add r0,r5,0x58
  mov r3,0x0
  str r4,[sp,0x4]
  bl loadsprite
  ;Load sprite 4
  mvn r0,0x0
  str r0,[sp,0x0]
  add r4,r6,0xb8
  ldr r1,=NFP2D
  ldr r2,=CUSTOM_SPRITE_04
  add r0,r5,0x84
  mov r3,0x0
  str r4,[sp,0x4]
  bl loadsprite
  ;Load sprite 6
  mvn r0,0x0
  str r0,[sp,0x0]
  add r4,r6,0xc0
  ldr r1,=NFP2D
  ldr r2,=CUSTOM_SPRITE_06
  add r0,r5,0xb0
  mov r3,0x0
  str r4,[sp,0x4]
  bl loadsprite
  ;Load sprite 7
  mvn r0,0x0
  str r0,[sp,0x0]
  add r4,r6,0xc8
  ldr r1,=NFP2D
  ldr r2,=CUSTOM_SPRITE_07
  add r0,r5,0xdc
  mov r3,0x0
  str r4,[sp,0x4]
  bl loadsprite
  ;Return
  mov r0,0x120
  add sp,sp,0xc
  strh r0,[r6,0x28]
  pop r4-r7,r15
  .pool

  CUSTOM_SPRITE_02:
  .asciiz "AV00_02.YCE"
  .align
  CUSTOM_SPRITE_03:
  .asciiz "AV00_03.YCE"
  .align
  CUSTOM_SPRITE_04:
  .asciiz "AV00_04.YCE"
  .align
  CUSTOM_SPRITE_05:
  .asciiz "AV00_05"
  .align
  CUSTOM_SPRITE_06:
  .asciiz "AV00_06.YCE"
  .align
  CUSTOM_SPRITE_07:
  .asciiz "AV00_07.YCE"
  .align
.endarea

;We reach this point of code if the main sprite doesn't match AV01_05, AV02_05 or AV11_01
.org 0x02034b70
  ;Original: movne r0,0x1000
  nop
  ;Original: addne r13,r13,0xc
  nop
  ;Original: strhne r0,[r6,0x28]
  nop
  ;Original: popne r4-r7,r15
  bne CUSTOM_SPRITE

;Tweak the amount of horizontal space that is cleaned when
;a speak sprite is cleared
.org 0x02032278
  ;Original: mov r0,0x80
  mov r0,0x90

;Move the MSG_ICON sprite a bit to the right to fit more text
.org 0x20321ec
  ;Original: mov r1,0xe0
  mov r1,0xe9

.close
