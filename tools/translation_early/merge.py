import json
import sys
from pathlib import Path

target = sys.argv[1]
assert target in {'101', '102', '103'}
path = Path('translation/arabic') / f'{target}.json'
data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
incoming = json.load(sys.stdin)
assert all(k.isdigit() and isinstance(v, str) for k, v in incoming.items())
data.update(incoming)
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(target, len(data))
