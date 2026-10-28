"""Apply reviewed Arabic corrections by record id with exact old/new substrings, and log them.

python -X utf8 tools/translation_qa/apply_fixes.py <fixes.json>
fixes.json: [{"id": "...", "old": "...", "new": "...", "reason": "..."}]. Each old must occur in the current
Arabic value; English, keys and indexes are never touched. Appends to translation/review/changes.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    fixes = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sources = {}
    for path in sorted((ROOT / "translation/source").glob("*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            sources[row["id"]] = (path.stem, str(row["index"]), row["en"])
    shards, log_path = {}, ROOT / "translation/review/changes.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    for fix in fixes:
        target, index, en = sources[fix["id"]]
        shard = shards.setdefault(target, json.loads((ROOT / "translation/arabic" / f"{target}.json").read_text(encoding="utf-8")))
        before = shard[index]
        if fix["old"] not in before:
            raise SystemExit(f"Old text not found in {fix['id']}: {fix['old']!r}")
        # Refuse a match glued to a neighbouring Arabic letter (e.g. شرطي inside الشرطي) unless explicitly allowed.
        letter = "[ء-يٱ-ۓ]"
        bounded = re.search(f"(?<!{letter}){re.escape(fix['old'])}(?!{letter})", before)
        if not bounded and not fix.get("allow_partial"):
            raise SystemExit(f"Old text is part of a larger Arabic word in {fix['id']}: {fix['old']!r}")
        after = before.replace(fix["old"], fix["new"])
        shard[index] = after
        log.append({"id": fix["id"], "en": en, "before": before, "after": after, "reason": fix["reason"]})
    for target, shard in shards.items():
        (ROOT / "translation/arabic" / f"{target}.json").write_text(json.dumps(shard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Applied {len(fixes)} fixes across {len(shards)} shards; log has {len(log)} entries")


if __name__ == "__main__":
    main()
