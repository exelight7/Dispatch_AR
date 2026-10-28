"""Round 017 read-only R8b frame-layout audit over asset_inspector JSON.
python -X utf8 frame_audit_017.py <installed_wbp.json> <original_wbp.json> <out.json>
Models UStruct::Link offsets (validated against the Run 2 minidump: Set Displayed Line LinearColor@200, ARLanguage@360,
ARText@432 land exactly on the dumped stack values) and classifies every call site against the UE4.27 VM return contract:
a callee with a CPF_ReturnParm writes through RESULT_PARAM; a bare top-level statement passes ProcessLocalScriptFunction's
uninitialized 64-byte scratch buffer (lea r8,[rsp+0x20] at RVA 0x115a933), which is only safe for trivially-copyable returns."""
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8')); orig = json.load(open(sys.argv[2], encoding='utf-8'))
E, I = d['Exports'], d['Imports']
SIZE = {'StrProperty': (16, 8), 'TextProperty': (24, 8), 'ObjectProperty': (8, 8), 'ClassProperty': (8, 8), 'ArrayProperty': (16, 8),
        'IntProperty': (4, 4), 'FloatProperty': (4, 4), 'BoolProperty': (1, 1), 'ByteProperty': (1, 1), 'EnumProperty': (1, 1),
        'DelegateProperty': (16, 4), 'NameProperty': (8, 4)}
STRUCT = {'SubtitleDisplayInfo': (184, 8), 'LinearColor': (16, 4), 'FormatArgumentData': (64, 8)}
NONTRIVIAL = {'StrProperty', 'TextProperty', 'ArrayProperty', 'StructProperty', 'MapProperty', 'SetProperty'}
def name(i): return I[-i - 1]['ObjectName'] if i < 0 else E[i - 1]['ObjectName']
def size_align(p):
    t = p['SerializedType']
    if t == 'StructProperty': return STRUCT.get(name(p['Struct']), (p['ElementSize'], 8))
    return SIZE[t]
def layout(e):
    off, rows, parms, ret, maxa = 0, [], 0, None, 1
    for p in e.get('LoadedProperties') or []:
        s, a = size_align(p); off = (off + a - 1) // a * a; maxa = max(maxa, a)
        fl = p['PropertyFlags']
        rows.append({'name': p['Name'], 'type': p['SerializedType'], 'offset': off, 'runtimeSize': s, 'serializedElementSize': p['ElementSize'],
                     'arrayDim': 1, 'flags': fl})
        if 'CPF_Parm' in fl: parms = off + s
        if 'CPF_ReturnParm' in fl: ret = {'offset': off, 'type': p['SerializedType'], 'size': s}
        off += s
    return {'properties': rows, 'PropertiesSize': off, 'ParmsSize': parms, 'ReturnValueOffset': ret['offset'] if ret else 'MAX_uint16',
            'return': ret, 'minAlignment': maxa}
funcs = {i + 1: e for i, e in enumerate(E) if 'Function' in e['$type']}
L = {i: layout(e) for i, e in funcs.items()}
origfuncs = {e['ObjectName'] for e in orig['Exports'] if 'Function' in e['$type']}
def op(x): return x['$type'].split('.')[-1].split(',')[0][3:] if isinstance(x, dict) and '$type' in x and '.EX_' in x['$type'] else None
findings = []
def visit(x, fn, idx, ctx):
    if isinstance(x, list):
        for y in x: visit(y, fn, idx, ctx)
        return
    if not isinstance(x, dict): return
    o = op(x)
    if o in ('LocalFinalFunction', 'FinalFunction', 'CallMath') and x['StackNode'] > 0:
        callee = x['StackNode']; lay = L[callee]
        params = [p for p in lay['properties'] if 'CPF_Parm' in p['flags'] and 'CPF_ReturnParm' not in p['flags']]
        argc = len(x['Parameters']); ret = lay['return']
        if ret is None: rc = 'NO_RETURN'
        elif ctx == 'statement': rc = 'BARE_STATEMENT_INTO_VM_SCRATCH_' + ('NONTRIVIAL' if ret['type'] in NONTRIVIAL else 'POD')
        else: rc = 'BOUND_' + ctx
        verdict = 'FRAME_LAYOUT_INVALID' if (argc != len(params) or rc.endswith('NONTRIVIAL')) else 'FRAME_LAYOUT_VALID'
        findings.append({'caller': E[fn - 1]['ObjectName'], 'instruction': idx, 'opcode': 'EX_' + o, 'callee': name(callee),
                         'args': argc, 'calleeParams': len(params), 'calleeReturn': ret, 'returnContext': rc, 'verdict': verdict})
    sub = 'arg'
    if o == 'Let': sub = 'Let'
    elif o in ('LetBool', 'LetObj'): sub = o
    elif o == 'JumpIfNot': sub = 'JumpIfNot_bool'
    elif o == 'Return': sub = 'Return'
    for k, v in x.items():
        if k == '$type': continue
        visit(v, fn, idx, sub if isinstance(v, dict) and op(v) else 'arg')
for fn, e in funcs.items():
    for idx, ins in enumerate(e.get('ScriptBytecode') or []):
        visit(ins, fn, idx, 'statement')
r8b = [f for f in funcs if E[f - 1]['ObjectName'] not in origfuncs or E[f - 1]['ObjectName'] in
       ('Set Displayed Line', 'Stop Displaying Line', 'Set Has Outline', 'ChangeTextToLarge', 'Set Wrap Text At', 'On Text Finished Letter by Letter Print')]
out = {'layouts': {E[f - 1]['ObjectName']: L[f] for f in r8b}, 'callSites': [c for c in findings if c['caller'] in {E[f - 1]['ObjectName'] for f in r8b}]}
out['invalid'] = [c for c in out['callSites'] if c['verdict'] != 'FRAME_LAYOUT_VALID']
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for c in out['invalid']: print('INVALID', c['caller'], c['instruction'], c['opcode'], c['callee'], c['returnContext'], 'args', c['args'], '/', c['calleeParams'])
print('call sites to script functions:', len(out['callSites']), 'invalid:', len(out['invalid']))
for f in r8b:
    l = L[f]; print('%-32s PS=%4d Parms=%3d Ret=%s' % (E[f - 1]['ObjectName'], l['PropertiesSize'], l['ParmsSize'], l['ReturnValueOffset']))
