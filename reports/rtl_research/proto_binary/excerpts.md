# Minimal binary excerpts

RVAs, build hash locked. Analyst aliases, not symbols.

## style_struct_registration

```asm
; 0x9a7470..0x9a7483
009a7470  lea      rdx, [rip + 0x3663f39]
009a7477  lea      rcx, [rip + 0x38a69ca]
009a747e  call     0x141150000
```

## char_decorator_class_registration

```asm
; 0x9a666d..0x9a669c
009a666d  lea      rdx, [rip + 0x28267fe]
009a6674  lea      rax, [rip + 0x9f5]
009a667b  mov      qword ptr [r11 - 0x28], rax
009a667f  lea      rax, [rip - 0x23bb76]
009a6686  mov      qword ptr [r11 - 0x30], rax
009a668a  lea      rax, [rip - 0x23a091]
009a6691  mov      qword ptr [r11 - 0x38], rax
009a6695  lea      rax, [rip + 0x2c4]
```

## char_decorator_object_constructor

```asm
; 0x9a6979..0x9a6983
009a6979  lea      rax, [rip + 0x2826ab0]
009a6980  mov      qword ptr [rbx], rax
```

## char_decorator_factory

```asm
; 0x99eaa0..0x99eaaa
0099eaa0  lea      rax, [rip + 0x282c539]
0099eaa7  mov      qword ptr [rdi], rax
```

## char_decorator_create_run

```asm
; 0x99e6e3..0x99e724
0099e6e3  lea      r8, [rbp + 0x280]
0099e6ea  mov      r9, qword ptr [rbp - 0x20]
0099e6ee  lea      rdx, [rbp + 0x10]
0099e6f2  mov      rcx, r13
0099e6f5  mov      ebx, dword ptr [r13 + 0x70]
0099e6f9  call     0x14099ef30
0099e6fe  mov      r9, rax
0099e701  mov      dword ptr [rsp + 0x28], ebx
0099e705  lea      rax, [rsp + 0x58]
0099e70a  lea      r8, [rsp + 0x48]
0099e70f  mov      qword ptr [rsp + 0x20], rax
0099e714  lea      rdx, [rbp + 0x280]
0099e71b  lea      rcx, [rbp - 0x80]
0099e71f  call     0x14099d0e0
```

## char_run_factory

```asm
; 0x99d13e..0x99d150
0099d13e  call     0x14130f7f0
0099d143  lea      rax, [rip + 0x282ddee]
0099d14a  xor      r15d, r15d
0099d14d  mov      qword ptr [rdi], rax
```

## char_run_paint

```asm
; 0x9a2d6f..0x9a2da3
009a2d6f  mov      ecx, dword ptr [rsp + 0x60]
009a2d73  xor      eax, eax
009a2d75  mov      r15d, dword ptr [rsp + 0x64]
009a2d7a  xorps    xmm8, xmm8
009a2d7e  sub      r15d, ecx
009a2d81  mov      qword ptr [rsp + 0x2c8], r14
009a2d89  mov      r14d, dword ptr [rbp + 0x240]
009a2d90  mov      r12d, eax
009a2d93  movss    dword ptr [rsp + 0x58], xmm8
009a2d9a  mov      dword ptr [rsp + 0x70], ecx
009a2d9e  mov      dword ptr [rsp + 0x54], r15d
; 0x9a2dd2..0x9a2dfc
009a2dd2  lea      eax, [rsi + 1]
009a2dd5  mov      dword ptr [rsp + 0x60], esi
009a2dd9  mov      dword ptr [rsp + 0x64], eax
009a2ddd  mov      eax, r12d
009a2de0  sub      eax, dword ptr [rdi + 0x304]
009a2de6  add      eax, ecx
009a2de8  movsxd   rcx, eax
009a2deb  mov      rax, qword ptr [rdi + 0x308]
009a2df2  shl      rcx, 5
009a2df6  movss    xmm1, dword ptr [rcx + rax + 0x10]
; 0x9a2f9c..0x9a2fc2
009a2f9c  movzx    eax, byte ptr [rbp + 0x10]
009a2fa0  lea      r9, [rsp + 0x60]
009a2fa5  mov      byte ptr [rsp + 0x28], al
009a2fa9  lea      r8, [rbp + 0xb0]
009a2fb0  mov      qword ptr [rsp + 0x20], rcx
009a2fb5  lea      rdx, [rbp]
009a2fb9  lea      rcx, [rbp - 0x20]
009a2fbd  call     0x14132ec90
; 0x9a33e3..0x9a341a
009a33e3  mov      rax, qword ptr [rbx]
009a33e6  call     qword ptr [rax + 0x38]
009a33e9  movaps   xmm10, xmm12
009a33ed  lea      rdx, [rbp + 0x38]
009a33f1  movaps   xmm9, xmm13
009a33f5  mov      rcx, rbx
009a33f8  addss    xmm10, dword ptr [rax]
009a33fd  addss    xmm9, dword ptr [rax + 4]
009a3403  mov      rax, qword ptr [rbx]
009a3406  addss    xmm10, dword ptr [rsp + 0x58]
009a340d  mulss    xmm9, xmm6
009a3412  mulss    xmm10, xmm6
009a3417  call     qword ptr [rax + 0x18]
; 0x9a353b..0x9a3567
009a353b  call     0x141237880
009a3540  mov      rcx, qword ptr [rbp - 0x20]
009a3544  call     0x1409ce980
009a3549  movss    xmm2, dword ptr [rsp + 0x58]
009a354f  mov      rbx, qword ptr [rbp - 0x18]
009a3553  test     rbx, rbx
009a3556  movd     xmm0, eax
009a355a  cvtdq2ps xmm0, xmm0
009a355d  addss    xmm2, xmm0
009a3561  movss    dword ptr [rsp + 0x58], xmm2
; 0x9a3591..0x9a35bb
009a3591  inc      esi
009a3593  movss    xmm7, dword ptr [rsp + 0x68]
009a3599  inc      r12d
009a359c  movss    xmm8, dword ptr [rsp + 0x58]
009a35a3  movss    xmm9, dword ptr [rsp + 0x6c]
009a35aa  mov      ecx, dword ptr [rsp + 0x70]
009a35ae  mov      dword ptr [rsp + 0x4c], esi
009a35b2  cmp      r12d, r15d
009a35b5  jl       0x1409a2dd2
```

## style_row_to_timing_map

```asm
; 0x9a4675..0x9a46e7
009a4675  movss    xmm0, dword ptr [rbx + 0x278]
009a467d  movss    dword ptr [rsp + 0x20], xmm0
009a4683  movss    xmm1, dword ptr [rbx + 0x27c]
009a468b  movss    dword ptr [rsp + 0x24], xmm1
009a4691  movzx    eax, byte ptr [rbx + 0x280]
009a4698  mov      byte ptr [rsp + 0x28], al
009a469c  movss    xmm0, dword ptr [rbx + 0x284]
009a46a4  movss    dword ptr [rsp + 0x2c], xmm0
009a46aa  movss    xmm1, dword ptr [rbx + 0x288]
009a46b2  movss    dword ptr [rsp + 0x30], xmm1
009a46b8  movss    xmm0, dword ptr [rbx + 0x28c]
009a46c0  movss    dword ptr [rsp + 0x34], xmm0
009a46c6  movss    xmm1, dword ptr [rbx + 0x290]
009a46ce  movss    dword ptr [rsp + 0x38], xmm1
009a46d4  movss    xmm0, dword ptr [rbx + 0x294]
009a46dc  movss    dword ptr [rsp + 0x3c], xmm0
009a46e2  call     0x14099b280
```

## style_timing_to_run_record

```asm
; 0x9a2278..0x9a22c0
009a2278  lea      rcx, [r12 + 0x7f8]
009a2280  call     0x1409a0440
009a2285  movsxd   rax, dword ptr [rbp + 0x67]
009a2289  cmp      eax, -1
009a228c  je       0x1409a22a0
009a228e  lea      rdx, [rax + rax*2]
009a2292  shl      rdx, 4
009a2296  add      rdx, qword ptr [r12 + 0x7f8]
009a229e  jmp      0x1409a22a3
009a22a0  mov      rdx, r14
009a22a3  test     rdx, rdx
009a22a6  lea      rax, [rdx + 8]
009a22aa  cmove    rax, r14
009a22ae  movups   xmm0, xmmword ptr [rax]
009a22b1  movups   xmmword ptr [rsi + 0x70], xmm0
009a22b5  movups   xmm1, xmmword ptr [rax + 0x10]
009a22b9  movups   xmmword ptr [rsi + 0x80], xmm1
```

## select_print_delay

```asm
; 0x9a089f..0x9a08bc
009a089f  cmp      byte ptr [rcx + 0x681], 0
009a08a6  movzx    esi, r8b
009a08aa  mov      rbx, rcx
009a08ad  je       0x1409a08bc
009a08af  movss    xmm0, dword ptr [rcx + 0x684]
009a08b7  jmp      0x1409a09a7
; 0x9a08ea..0x9a097b
009a08ea  cmp      byte ptr [rsp + 0x98], 0
009a08f2  je       0x1409a096e
009a08f4  test     sil, sil
009a08f7  je       0x1409a096e
009a08f9  cmp      sil, 2
009a08fd  jne      0x1409a090e
009a08ff  mov      rax, qword ptr [rbx + 0x7a8]
009a0906  movss    xmm6, dword ptr [rax + rdi + 0x7c]
009a090c  jmp      0x1409a097b
009a090e  cmp      sil, 1
009a0912  jne      0x1409a0926
009a0914  mov      rax, qword ptr [rbx + 0x7a8]
009a091b  movss    xmm6, dword ptr [rax + rdi + 0x8c]
009a0924  jmp      0x1409a097b
009a0926  cmp      sil, 4
009a092a  jne      0x1409a093e
009a092c  mov      rax, qword ptr [rbx + 0x7a8]
009a0933  movss    xmm6, dword ptr [rax + rdi + 0x80]
009a093c  jmp      0x1409a097b
009a093e  cmp      sil, 5
009a0942  jne      0x1409a0956
009a0944  mov      rax, qword ptr [rbx + 0x7a8]
009a094b  movss    xmm6, dword ptr [rax + rdi + 0x84]
009a0954  jmp      0x1409a097b
009a0956  cmp      sil, 3
009a095a  jne      0x1409a096e
009a095c  mov      rax, qword ptr [rbx + 0x7a8]
009a0963  movss    xmm6, dword ptr [rax + rdi + 0x88]
009a096c  jmp      0x1409a097b
009a096e  mov      rax, qword ptr [rbx + 0x7a8]
009a0975  movss    xmm6, dword ptr [rax + rdi + 0x74]
```

## advance_reveal_index

```asm
; 0x99ce5f..0x99ce8c
0099ce5f  inc      dword ptr [rbx + 0x7d4]
0099ce65  mov      eax, dword ptr [rbx + 0x7d0]
0099ce6b  inc      eax
0099ce6d  mov      dword ptr [rbx + 0x7d0], eax
0099ce73  mov      ecx, dword ptr [rdi + 8]
0099ce76  test     ecx, ecx
0099ce78  lea      edx, [rcx - 2]
0099ce7b  mov      ecx, eax
0099ce7d  cmove    edx, ebp
0099ce80  sub      ecx, dword ptr [rdi + 0x90]
0099ce86  cmp      ecx, edx
0099ce88  je       0x14099ceb4
0099ce8a  jmp      0x14099ceba
```

## process_reveal_budget

```asm
; 0x9a39a8..0x9a39c6
009a39a8  comiss   xmm7, dword ptr [r14 + 0x7e4]
009a39b0  mov      qword ptr [rsp + 0x138], rbx
009a39b8  movaps   xmmword ptr [rsp + 0xf0], xmm6
009a39c0  jb       0x1409a3bf6
; 0x9a3a0d..0x9a3a30
009a3a0d  inc      eax
009a3a0f  mov      rcx, r14
009a3a12  cmp      eax, dword ptr [r12]
009a3a16  jge      0x1409a3b7f
009a3a1c  movsxd   r13, dword ptr [r14 + 0x7d8]
009a3a23  inc      esi
009a3a25  mov      dword ptr [rsp + 0x48], esi
009a3a29  call     qword ptr [r8 + 0x388]
; 0x9a3b11..0x9a3b7f
009a3b11  mov      rax, qword ptr [r14]
009a3b14  mov      edx, r13d
009a3b17  mov      r8d, dword ptr [r15]
009a3b1a  mov      rcx, r14
009a3b1d  subss    xmm7, dword ptr [r14 + 0x7e4]
009a3b26  call     qword ptr [rax + 0x390]
009a3b2c  mov      rcx, qword ptr [r14]
009a3b2f  lea      rbx, [r14 + 0x7e8]
009a3b36  movzx    r8d, al
009a3b3a  mov      byte ptr [rbx], al
009a3b3c  mov      edx, r13d
009a3b3f  mov      r9, qword ptr [rcx + 0x368]
009a3b46  mov      rcx, r14
009a3b49  call     r9
009a3b4c  mov      rax, qword ptr [r14]
009a3b4f  xor      r8d, r8d
009a3b52  mov      edx, r13d
009a3b55  movss    dword ptr [r14 + 0x7e4], xmm0
009a3b5e  mov      rcx, r14
009a3b61  call     qword ptr [rax + 0x368]
009a3b67  comiss   xmm0, dword ptr [r14 + 0x7e4]
009a3b6f  jae      0x1409a3a77
009a3b75  mov      r13b, 1
009a3b78  mov      byte ptr [rsp + 0x30], r13b
009a3b7d  jmp      0x1409a3b95
; 0x9a3b95..0x9a3ba3
009a3b95  comiss   xmm7, dword ptr [r14 + 0x7e4]
009a3b9d  jae      0x1409a39f0
; 0x9a3d62..0x9a3d9b
009a3d62  movss    xmm0, dword ptr [rip + 0x277e43e]
009a3d6a  lea      rdx, [r14 + 0x7f0]
009a3d71  movss    dword ptr [rsp + 0x28], xmm0
009a3d77  lea      r8, [rbp - 0x69]
009a3d7b  movaps   xmm3, xmm6
009a3d7e  mov      byte ptr [rsp + 0x20], 0
009a3d83  mov      rcx, rbx
009a3d86  mov      qword ptr [rbp - 0x51], 0
009a3d8e  mov      qword ptr [rbp - 0x49], r15
009a3d92  mov      qword ptr [rbp - 0x39], r15
009a3d96  call     0x142739fa0
```

## print_letter_by_letter

```asm
; 0x9a3fd6..0x9a3ff7
009a3fd6  mov      r9, qword ptr [rcx + 0x368]
009a3fdd  mov      rcx, rbx
009a3fe0  call     r9
009a3fe3  xorps    xmm1, xmm1
009a3fe6  movss    dword ptr [rbx + 0x7e4], xmm0
009a3fee  comiss   xmm0, xmm1
009a3ff1  jbe      0x1409a4222
; 0x9a4222..0x9a422e
009a4222  mov      rax, qword ptr [rbx]
009a4225  mov      rcx, rbx
009a4228  call     qword ptr [rax + 0x358]
```

## exec_PrintLetterByLetter

```asm
; 0x9a7905..0x9a790f
009a7905  mov      rax, qword ptr [rcx]
009a7908  jmp      qword ptr [rax + 0x308]
```

## shaped_range_helper

```asm
; 0x132ed34..0x132ed48
0132ed34  mov      eax, dword ptr [r14]
0132ed37  cmp      dword ptr [rsi], eax
0132ed39  jne      0x14132ed48
0132ed3b  mov      eax, dword ptr [r14 + 4]
0132ed3f  cmp      dword ptr [rsi + 4], eax
0132ed42  je       0x14132f030
; 0x132ee66..0x132ee85
0132ee66  xor      ebx, ebx
0132ee68  mov      r8, qword ptr [rbp - 0x80]
0132ee6c  lea      rdx, [rsp + 0x58]
0132ee71  mov      r14, qword ptr [rsp + 0x40]
0132ee76  mov      rcx, r14
0132ee79  mov      r9d, dword ptr [r8 + 4]
0132ee7d  mov      r8d, dword ptr [r8]
0132ee80  call     0x1411d74b0
```

## slice_advance_scalar

```asm
; 0x9ce980..0x9ce984
009ce980  mov      eax, dword ptr [rcx + 0x40]
009ce983  ret      
```
