"""Read-only Kismet pretty-printer over asset_inspector JSON. python -X utf8 kprint.py <asset.json> <function name>..."""
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
E, I = d['Exports'], d['Imports']
def ref(i):
    if i is None or i == 0: return 'null'
    if i < 0:
        o = I[-i - 1]; outer = o.get('OuterIndex', 0)
        return (I[-outer - 1]['ObjectName'] + '.' if outer < 0 else '') + o['ObjectName']
    return 'export%d:%s' % (i, E[i - 1]['ObjectName'])
def prop(p):
    p = p.get('New', p) if isinstance(p, dict) else p
    if not isinstance(p, dict): return str(p)
    return '%s@%s' % ('.'.join(p.get('Path') or []) or '-', ref(p.get('ResolvedOwner')))
def ex(x):
    if x is None: return 'None'
    if not isinstance(x, dict): return repr(x)
    t = x['$type'].split('.')[-1].split(',')[0].replace('EX_', '')
    f = {k: v for k, v in x.items() if k != '$type'}
    if t in ('LocalVariable', 'InstanceVariable', 'LocalOutVariable', 'DefaultVariable'): return '%s(%s)' % (t[:-8] or t, prop(f['Variable']))
    if t in ('IntConst', 'FloatConst', 'ByteConst', 'StringConst', 'UnicodeStringConst', 'NameConst', 'Int64Const'): return '%s(%r)' % (t, f.get('Value'))
    if t == 'ObjectConst': return 'Obj(%s)' % ref(f['Value'])
    if t in ('True', 'False', 'Nothing', 'NoObject', 'Self', 'EndOfScript', 'PopExecutionFlow', 'EndFunctionParms'): return t
    if t in ('CallMath', 'LocalFinalFunction', 'FinalFunction'): return '%s %s(%s)' % (t, ref(f['StackNode']), ', '.join(ex(a) for a in f['Parameters']))
    if t in ('VirtualFunction', 'LocalVirtualFunction'): return '%s %s(%s)' % (t, f['VirtualFunctionName'], ', '.join(ex(a) for a in f['Parameters']))
    if t == 'Let': return 'Let[%s] %s = %s' % (prop(f['Value']), ex(f['Variable']), ex(f['Expression']))
    if t in ('LetBool', 'LetObj', 'LetWeakObjPtr', 'LetDelegate', 'LetMulticastDelegate'): return '%s %s = %s' % (t, ex(f['VariableExpression']), ex(f['AssignmentExpression']))
    if t == 'LetValueOnPersistentFrame': return 'LetPF[%s] = %s' % (prop(f['DestinationProperty']), ex(f['AssignmentExpression']))
    if t in ('Context', 'Context_FailSilent', 'ClassContext'): return '%s{%s}[rv=%s skip=%s].%s' % (t, ex(f['ObjectExpression']), prop(f['RValuePointer']), f['Offset'], ex(f['ContextExpression']))
    if t == 'Return': return 'Return ' + ex(f['ReturnExpression'])
    if t == 'Jump': return 'Jump @%s' % f['CodeOffset']
    if t == 'JumpIfNot': return 'JumpIfNot @%s !(%s)' % (f['CodeOffset'], ex(f['BooleanExpression']))
    if t == 'StructConst': return 'Struct %s(%s)' % (ref(f['Struct']), ', '.join(ex(a) for a in f['Value']))
    if t == 'StructMemberContext': return 'Member[%s](%s)' % (prop(f['StructMemberExpression']), ex(f['StructExpression']))
    if t == 'BindDelegate': return 'BindDelegate %s(%s, %s)' % (f['FunctionName'], ex(f['Delegate']), ex(f['ObjectTerm']))
    if t == 'PushExecutionFlow': return 'PushFlow @%s' % f['PushingAddress']
    if t == 'SetArray': return 'SetArray %s = [%s]' % (ex(f.get('AssigningProperty')), ', '.join(ex(a) for a in f['Elements']))
    if t in ('TextConst',): return 'TextConst(%s)' % json.dumps(f)[:80]
    return '%s%s' % (t, json.dumps({k: (ex(v) if isinstance(v, dict) and '$type' in v and 'EX_' in v['$type'] else v) for k, v in f.items()}, ensure_ascii=False)[:300])
for name in sys.argv[2:]:
    e = next(x for x in E if x['ObjectName'] == name)
    print('=== %s  flags=%s' % (name, e.get('FunctionFlags')))
    for k, x in enumerate(e['ScriptBytecode']): print('%4d  %s' % (k, ex(x)))
