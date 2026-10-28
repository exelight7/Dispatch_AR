"""Round 017 read-only: decode the Run 2 minidump stack against the audited Set Displayed Line frame layout.
python -X utf8 -I tools/r8b_017/dump_frame_017.py <UE4Minidump.dmp> <r8b_frame_audit_017.json> <out.json>"""
import json, struct, sys
d = open(sys.argv[1], 'rb').read()
n, rva = struct.unpack_from('<II', d, 8)
S = {struct.unpack_from('<I', d, rva + 12 * i)[0]: struct.unpack_from('<II', d, rva + 12 * i + 4) for i in range(n)}
M = []
if 5 in S:
    _, r = S[5]; k, = struct.unpack_from('<I', d, r)
    M += [struct.unpack_from('<QII', d, r + 4 + 16 * i) for i in range(k)]
if 9 in S:
    _, r = S[9]; k, base = struct.unpack_from('<QQ', d, r); o = base
    for i in range(k):
        st, ds = struct.unpack_from('<QQ', d, r + 16 + 16 * i); M.append((st, ds, o)); o += ds
def rd(a, size):
    for st, ds, rv in M:
        if st <= a and a + size <= st + ds: return d[rv + a - st: rv + a - st + size]
    raise KeyError(hex(a))
q = lambda a: struct.unpack('<Q', rd(a, 8))[0]
_, r = S[6]; csz, crva = struct.unpack_from('<II', d, r + 8 + 4 + 4 + 8 + 8 + 4 + 4 + 15 * 8)
regs = dict(zip(['Rax', 'Rcx', 'Rdx', 'Rbx', 'Rsp', 'Rbp'], struct.unpack_from('<6Q', d, crva + 0x78)))
layout = {p['name']: p for p in json.load(open(sys.argv[2], encoding='utf-8'))['layouts']['Set Displayed Line']['properties']}
frame = regs['Rbx']                       # FFrame& Stack of ProcessLocalScriptFunction (Code at +0x20)
scratch = regs['Rsp'] + 0x20              # lea r8,[rsp+0x20] at RVA 0x115a933: RESULT for every top-level statement
# Locals base: anchor the audited offset of CallFunc_Conv_ColorToLinearColor_ReturnValue on the only LinearColor-looking run below the frame.
base = next(a - layout['CallFunc_Conv_ColorToLinearColor_ReturnValue']['offset'] for a in range(frame - 0x400, frame, 4)
            if all(0.0 < f <= 1.0 for f in struct.unpack('<4f', rd(a, 16))) and struct.unpack('<f', rd(a + 12, 4))[0] == 1.0)
def fstring(a):
    data, num, mx = q(a), *struct.unpack('<ii', rd(a + 8, 8))
    return {'data': hex(data), 'num': num, 'max': mx}
locals_ = {nme: dict(offset=p['offset'], address=hex(base + p['offset'])) for nme, p in layout.items()}
for nme in ('ARLanguage', 'ARPlain', 'ARSpeaker', 'ARMarkup'): locals_[nme]['fstring'] = fstring(base + layout[nme]['offset'])
for nme in ('Temp_byte_Variable', 'Temp_byte_Variable_1'): locals_[nme]['byte'] = rd(base + layout[nme]['offset'], 1)[0]
for nme in ('CallFunc_GetGameInstanceSubsystem_ReturnValue_1', 'CallFunc_GetCloudSettings_ReturnValue_1'): locals_[nme]['qword'] = hex(q(base + layout[nme]['offset']))
locals_['CallFunc_GetOptionValue_ReturnValue']['float'] = struct.unpack('<f', rd(base + layout['CallFunc_GetOptionValue_ReturnValue']['offset'], 4))[0]
artext = base + layout['ARText']['offset']; markup = locals_['ARMarkup']['fstring']
text = rd(artext, markup['num'] * 2).decode('utf-16le')
out = {'registers': {k: hex(v) for k, v in regs.items()}, 'FFrame': hex(frame), 'FFrame_Code_field': hex(q(frame + 0x20)),
       'FFrame_Code_equals_Rax': q(frame + 0x20) == regs['Rax'], 'localsBase': hex(base), 'locals': locals_,
       'scratchBuffer': {'address': hex(scratch), 'asFString': fstring(scratch)},
       'scratchData_equals_ARText': q(scratch) == artext, 'scratchNum_equals_ARMarkupNum': struct.unpack('<i', rd(scratch + 8, 4))[0] == markup['num'],
       'textAtARText': text, 'textBytes': len(text) * 2, 'textEnd': hex(artext + len(text) * 2), 'overlapsFFrame': artext + len(text) * 2 > frame}
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for k in ('FFrame', 'FFrame_Code_field', 'FFrame_Code_equals_Rax', 'localsBase', 'scratchBuffer', 'scratchData_equals_ARText', 'scratchNum_equals_ARMarkupNum', 'textEnd', 'overlapsFFrame'): print(k, out[k])
print('ARText @', locals_['ARText']['address'], 'ARMarkup', markup, 'Temp bytes', locals_['Temp_byte_Variable']['byte'], locals_['Temp_byte_Variable_1']['byte'],
      'opacity', locals_['CallFunc_GetOptionValue_ReturnValue']['float'], 'instr69/70 targets', locals_['CallFunc_GetGameInstanceSubsystem_ReturnValue_1']['qword'], locals_['CallFunc_GetCloudSettings_ReturnValue_1']['qword'])
print('text:', text)
