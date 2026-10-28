"""Round 019 independent frame/metadata audit of the R8b repair (read-only; asset_inspector JSON in, JSON out).
python -X utf8 -I tools/r8b_019/frame_audit_019.py <before.json> <after.json> <native_returns_019.json> <before_inventory.json> <after_inventory.json> <original_wbp.json> <out.json>

Layout model = round 017's UStruct::Link model (tools/r8b_017/frame_audit_017.py), validated against the Run 2 minidump.
Call rule, implemented separately from the C# validator: a top-level statement passes ProcessLocalScriptFunction's
uninitialized 64-byte scratch buffer as RESULT_PARAM, so a statement-level call may only return void, a scalar, or a struct
whose native thunk plainly stores it. EX_Context forwards its own RESULT_PARAM to the context expression.
"""
import json
import sys

SIZE = {'StrProperty': (16, 8), 'TextProperty': (24, 8), 'ObjectProperty': (8, 8), 'ClassProperty': (8, 8), 'ArrayProperty': (16, 8),
        'IntProperty': (4, 4), 'FloatProperty': (4, 4), 'BoolProperty': (1, 1), 'ByteProperty': (1, 1), 'EnumProperty': (1, 1),
        'DelegateProperty': (16, 4), 'NameProperty': (8, 4)}
STRUCT = {'SubtitleDisplayInfo': (184, 8), 'LinearColor': (16, 4), 'FormatArgumentData': (64, 8), 'Geometry': (56, 4)}
SCALAR = {'Bool', 'Byte', 'Int8', 'Int16', 'Int', 'Int64', 'UInt16', 'UInt32', 'UInt64', 'Float', 'Double', 'Name', 'Object', 'Class', 'Enum'}
CALLS = {'LocalFinalFunction', 'FinalFunction', 'CallMath', 'VirtualFunction', 'LocalVirtualFunction', 'CallMulticastDelegate'}
TIMING = 'Build Arabic Timing'
R8B_ORIGINAL = ('Set Displayed Line', 'Stop Displaying Line', 'Set Has Outline', 'ChangeTextToLarge', 'Set Wrap Text At',
                'On Text Finished Letter by Letter Print')


def op(x): return x['$type'].split('.')[-1].split(',')[0][3:] if isinstance(x, dict) and '.EX_' in x.get('$type', '') else None


class Asset:
    def __init__(self, path):
        self.d = json.load(open(path, encoding='utf-8')); self.E, self.I = self.d['Exports'], self.d['Imports']
        self.funcs = {i + 1: e for i, e in enumerate(self.E) if 'FunctionExport' in e['$type']}

    def name(self, i): return self.I[-i - 1]['ObjectName'] if i < 0 else self.E[i - 1]['ObjectName']

    def layout(self, e):
        off, rows, parms, ret, nparms = 0, [], 0, None, 0
        for p in e.get('LoadedProperties') or []:
            t = p['SerializedType']
            s, a = STRUCT.get(self.name(p['Struct']), (p['ElementSize'], 8)) if t == 'StructProperty' else SIZE[t]
            off = (off + a - 1) // a * a; fl = p['PropertyFlags']
            rows.append({'name': p['Name'], 'type': t, 'flags': fl, 'offset': off, 'runtimeSize': s, 'alignment': a,
                         'ElementSize': p['ElementSize'], 'ArrayDim': {'TArray': 1}.get(p.get('ArrayDim'), p.get('ArrayDim')),
                         'role': 'return' if 'CPF_ReturnParm' in fl else 'parameter' if 'CPF_Parm' in fl else 'local'})
            if 'CPF_Parm' in fl: parms, nparms = off + s, nparms + 1
            if 'CPF_ReturnParm' in fl: ret = {'offset': off, 'type': t, 'size': s}
            off += s
        return {'PropertiesSize': off, 'ParmsSize': parms, 'NumParms': nparms, 'ReturnValueOffset': ret['offset'] if ret else 'MAX_uint16',
                'return': ret, 'properties': rows}

    def signature(self, x, natives):
        s = x.get('StackNode'); v = x.get('VirtualFunctionName')
        local = s if isinstance(s, int) and s > 0 else next((i for i, e in self.funcs.items() if v and e['ObjectName'] == v), None)
        if local:
            lay = self.layout(self.E[local - 1])
            return self.E[local - 1]['ObjectName'], (lay['return'] or {}).get('type', 'void').replace('Property', ''), \
                sum(1 for p in lay['properties'] if p['role'] == 'parameter'), False
        if isinstance(s, int) and s < 0:
            imp = self.I[-s - 1]; o = imp['OuterIndex']; key = (self.I[-o - 1]['ObjectName'] + '.' if o < 0 else '') + imp['ObjectName']
        else: key = v
        e = natives['functions'].get(key)
        if not e or e['return'] == 'UNRESOLVED': return key, 'UNRESOLVED', None, False
        return key, e['return'] or 'void', len(e['params']) if e['params'] is not None else None, bool(e.get('trivial_store', {}).get('trivial'))

    def call_sites(self, natives):
        rows = []

        def visit(x, ctx, fn, idx):
            if isinstance(x, list):
                for y in x: visit(y, ctx, fn, idx)
                return
            if not isinstance(x, dict): return
            o = op(x)
            if o in CALLS:
                callee, ret, nparams, trivial = self.signature(x, natives)
                scratch = ctx == 'statement'
                unsafe = scratch and ret not in SCALAR | {'void'} and not (ret == 'Struct' and trivial)
                bad_args = nparams is not None and nparams != len(x['Parameters'])
                rows.append({'caller': self.E[fn - 1]['ObjectName'], 'instruction': idx, 'opcode': 'EX_' + o, 'callee': callee, 'return': ret,
                             'resultStorage': 'VM_SCRATCH_UNCONSTRUCTED' if scratch else 'BOUND_' + ctx, 'args': len(x['Parameters']),
                             'calleeParams': nparams, 'verdict': 'FRAME_LAYOUT_INVALID' if unsafe or bad_args or ret == 'UNRESOLVED' else 'FRAME_LAYOUT_VALID'})
            for k, v in x.items():
                if k == '$type': continue
                if o in ('Context', 'Context_FailSilent', 'ClassContext') and k == 'ContextExpression': sub = ctx
                elif o == 'Let': sub = 'Let'
                elif o in ('LetBool', 'LetObj', 'LetValueOnPersistentFrame'): sub = o
                elif o == 'JumpIfNot': sub = 'JumpIfNot_bool'
                elif o == 'Return': sub = 'Return'
                else: sub = 'arg'
                visit(v, sub, fn, idx)
        for fn, e in self.funcs.items():
            for idx, ins in enumerate(e.get('ScriptBytecode') or []): visit(ins, 'statement', fn, idx)
        return rows


def operands(asset, fi):
    """FFieldPath property operands owned by function fi in its own bytecode."""
    names = []

    def walk(x):
        if isinstance(x, list):
            for y in x: walk(y)
        elif isinstance(x, dict):
            if 'FFieldPath' in x.get('$type', '') and x.get('ResolvedOwner') == fi and x.get('Path'): names.append(x['Path'][0])
            for v in x.values(): walk(v)
    walk(asset.E[fi - 1].get('ScriptBytecode'))
    return names


def bytecode_sizes(inv, fi):
    f = next(x for x in inv if x['export'] == fi)
    return {'logical': sum(i['logicalSize'] for i in f['instructions']), 'serialized': sum(i['serializedSize'] for i in f['instructions']),
            'instructions': len(f['instructions']), 'sha256': f['bytecodeSha256']}


def main(before_p, after_p, natives_p, inv_b, inv_a, original_p, out_p):
    B, A, natives = Asset(before_p), Asset(after_p), json.load(open(natives_p, encoding='utf-8'))
    ib, ia = json.load(open(inv_b, encoding='utf-8')), json.load(open(inv_a, encoding='utf-8'))
    fi = next(i for i, e in A.funcs.items() if e['ObjectName'] == TIMING)
    assert B.E[fi - 1]['ObjectName'] == TIMING
    record = {}
    for label, asset, inv in (('before', B, ib), ('after', A, ia)):
        e = asset.E[fi - 1]; lay = asset.layout(e); code = e['ScriptBytecode']
        ops = operands(asset, fi); declared = {p['name'] for p in lay['properties']}
        record[label] = {'FunctionFlags': e['FunctionFlags'], 'PropertiesSize': lay['PropertiesSize'], 'ParmsSize': lay['ParmsSize'],
                         'NumParms': lay['NumParms'], 'ReturnValueOffset': lay['ReturnValueOffset'], 'ScriptBytecodeSize': e['ScriptBytecodeSize'],
                         'bytecode': bytecode_sizes(inv, fi),
                         'parameter_table': [p for p in lay['properties'] if p['role'] != 'local'],
                         'local_property_table': [p for p in lay['properties'] if p['role'] == 'local'],
                         'return_statements': [{'instruction': k, 'expression': op(x['ReturnExpression'])} for k, x in enumerate(code) if op(x) == 'Return'],
                         'bytecode_property_operands': sorted(set(ops)), 'unresolved_property_operands': sorted(set(ops) - declared)}
    b, a = record['before'], record['after']
    checks = {
        'return_property_removed': b['ReturnValueOffset'] == 32 and a['ReturnValueOffset'] == 'MAX_uint16' and not any(p['role'] == 'return' for p in a['parameter_table']),
        'has_out_parms_cleared': 'FUNC_HasOutParms' in b['FunctionFlags'] and 'FUNC_HasOutParms' not in a['FunctionFlags']
                                 and set(b['FunctionFlags'].split(', ')) - set(a['FunctionFlags'].split(', ')) == {'FUNC_HasOutParms'},
        'no_out_parameters_left': not any('CPF_OutParm' in p['flags'] for p in a['parameter_table'] + a['local_property_table']),
        'parameters_unchanged': [(p['name'], p['type'], p['flags'], p['offset']) for p in a['parameter_table']]
                                == [(p['name'], p['type'], p['flags'], p['offset']) for p in b['parameter_table'] if p['role'] == 'parameter'],
        'locals_same_order_shifted_by_return_size': [(p['name'], p['type'], p['flags'], p['ElementSize'], p['ArrayDim']) for p in a['local_property_table']]
                                == [(p['name'], p['type'], p['flags'], p['ElementSize'], p['ArrayDim']) for p in b['local_property_table']]
                                and all(x['offset'] == y['offset'] - 16 for x, y in zip(a['local_property_table'], b['local_property_table'])),
        'sizes': (b['PropertiesSize'], b['ParmsSize'], a['PropertiesSize'], a['ParmsSize']) == (216, 48, 200, 32),
        'element_size_matches_runtime': all(p['ElementSize'] == p['runtimeSize'] and p['ArrayDim'] == 1 for p in a['parameter_table'] + a['local_property_table']),
        'single_return_nothing': b['return_statements'] == [{'instruction': 83, 'expression': 'LocalVariable'}] and a['return_statements'] == [{'instruction': 83, 'expression': 'Nothing'}],
        'bytecode_shrinks_by_one_operand': b['ScriptBytecodeSize'] - a['ScriptBytecodeSize'] == 8 and a['bytecode']['logical'] == a['ScriptBytecodeSize']
                                          and b['bytecode']['logical'] == b['ScriptBytecodeSize'] and a['bytecode']['instructions'] == b['bytecode']['instructions'],
        'property_operands_resolve': not a['unresolved_property_operands'] and 'ReturnValue' not in a['bytecode_property_operands'],
    }
    shipped = {x['ObjectName'] for x in json.load(open(original_p, encoding='utf-8'))['Exports'] if 'FunctionExport' in x['$type']}
    r8b = lambda asset: [f for f, e in asset.funcs.items() if e['ObjectName'] not in shipped or e['ObjectName'] in R8B_ORIGINAL]
    layouts = {lab: {asset.E[f - 1]['ObjectName']: {k: v for k, v in asset.layout(asset.E[f - 1]).items() if k != 'properties'} for f in r8b(asset)}
               for lab, asset in (('before', B), ('after', A))}
    changed = sorted(n for n in layouts['after'] if layouts['after'][n] != layouts['before'].get(n))
    checks['only_timing_layout_changed'] = changed == [TIMING]
    sites = {lab: asset.call_sites(natives) for lab, asset in (('before', B), ('after', A))}
    invalid = {lab: [s for s in rows if s['verdict'] != 'FRAME_LAYOUT_VALID'] for lab, rows in sites.items()}
    checks['run2_site_invalid_before'] = [(s['caller'], s['instruction'], s['callee'], s['return']) for s in invalid['before']] == [('Set Displayed Line', 66, TIMING, 'Str')]
    checks['zero_invalid_after'] = not invalid['after']
    after66 = [s for s in sites['after'] if s['caller'] == 'Set Displayed Line' and s['instruction'] == 66]
    checks['site66_after_void_statement'] = [(s['callee'], s['return'], s['resultStorage']) for s in after66] == [(TIMING, 'void', 'VM_SCRATCH_UNCONSTRUCTED')]
    # English isolation: every other function is identical to the Run 1-proven 012 build, and the only Build Arabic Timing call
    # is unreachable when bArabic is false (both JumpIfNot outcomes explored except the language gate).
    same = lambda f: all(B.E[f - 1].get(k) == A.E[f - 1].get(k) for k in ('ScriptBytecode', 'LoadedProperties', 'FunctionFlags'))
    checks['all_other_functions_identical_to_012'] = [A.E[f - 1]['ObjectName'] for f in A.funcs if not same(f)] == [TIMING]
    sdl = next(i for i, e in A.funcs.items() if e['ObjectName'] == 'Set Displayed Line'); code = A.E[sdl - 1]['ScriptBytecode']
    at = {x['logicalOffset']: x['instruction'] for x in next(f for f in ia if f['export'] == sdl)['instructions']}
    gate = lambda n: op(n) == 'InstanceVariable' and n['Variable']['New']['Path'] == ['bArabic']
    pushed = [at[x['PushingAddress']] for x in code if op(x) == 'PushExecutionFlow']

    def reachable(arabic):
        seen, todo = set(), [0]
        while todo:
            pc = todo.pop()
            if pc in seen or pc >= len(code): continue
            seen.add(pc); x = code[pc]; o = op(x)
            if o == 'Jump': todo.append(at[x['CodeOffset']])
            elif o == 'JumpIfNot':
                if not gate(x['BooleanExpression']) or not arabic: todo.append(at[x['CodeOffset']])
                if not gate(x['BooleanExpression']) or arabic: todo.append(pc + 1)
            elif o == 'PopExecutionFlow': todo.extend(pushed)
            elif o not in ('Return', 'EndOfScript'): todo.append(pc + 1)
        return seen
    english, arabic = reachable(False), reachable(True)
    checks['timing_call_unreachable_from_english'] = 66 not in english and 66 in arabic and op(code[66]) == 'LocalFinalFunction'
    out = {'function': TIMING, 'export': fi, 'metadata': record, 'checks': checks, 'layouts': layouts, 'layout_changes': changed,
           'english_isolation': {'set_displayed_line_english_reachable': len(english), 'arabic_reachable': len(arabic),
                                 'english_reaches_instruction_66': 66 in english},
           'call_sites': {lab: len(rows) for lab, rows in sites.items()},
           'statement_level_calls_after': [s for s in sites['after'] if s['resultStorage'] == 'VM_SCRATCH_UNCONSTRUCTED'],
           'invalid': invalid, 'verdict': 'FRAME_LAYOUT_AUDIT_PASS' if all(checks.values()) else 'FRAME_LAYOUT_AUDIT_FAIL'}
    json.dump(out, open(out_p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    for k, v in checks.items(): print('%-45s %s' % (k, 'PASS' if v else 'FAIL'))
    print('before', b['PropertiesSize'], b['ParmsSize'], b['ReturnValueOffset'], '| after', a['PropertiesSize'], a['ParmsSize'], a['ReturnValueOffset'])
    print('call sites', out['call_sites'], 'invalid before', len(invalid['before']), 'after', len(invalid['after']))
    print(out['verdict'])
    return 0 if out['verdict'] == 'FRAME_LAYOUT_AUDIT_PASS' else 1


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:8]))
