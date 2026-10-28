"""Export / record literary review batches.

python -X utf8 tools/translation_qa/review_batch.py export <category> <start> <count>
    prints unreviewed queue records of that category (by priority) in a compact form, with the
    previous/next record of the same source asset for dialogue context.
python -X utf8 tools/translation_qa/review_batch.py record <verdicts.json>
    verdicts.json: [{"id":..., "status": "REVIEWED_OK"|"CHANGED_AFTER_REVIEW"|"NEEDS_CONTEXT"|"BLOCKED", "note": ...}]
    merges into translation/review/review_log.json (CHANGED requires a matching translation/review/changes.json entry).
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "translation/review/review_queue.json"
LOG = ROOT / "translation/review/review_log.json"
STATUSES = {"REVIEWED_OK", "CHANGED_AFTER_REVIEW", "NEEDS_CONTEXT", "BLOCKED"}


def flat(text):
    return text.replace("\r", "").replace("\n", "⏎")


def export(category, start, count):
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    log = {e["id"] for e in json.loads(LOG.read_text(encoding="utf-8"))} if LOG.exists() else set()
    picked = [q for q in queue if category in q["categories"] and q["id"] not in log][start:start + count]
    for n, q in enumerate(picked):
        ctx = q["context"][0].rsplit("/", 1)[-1][:70] if q["context"] else ""
        print(f"#{n} {q['id']} [{q['speaker'] or '-'}] {{{ctx}}}")
        print(f"  EN: {flat(q['en'])}")
        print(f"  AR: {flat(q['ar'])}")


def record(path):
    verdicts = json.loads(Path(path).read_text(encoding="utf-8"))
    log = {e["id"]: e for e in json.loads(LOG.read_text(encoding="utf-8"))} if LOG.exists() else {}
    changes = {c["id"] for c in json.loads((ROOT / "translation/review/changes.json").read_text(encoding="utf-8"))}
    for v in verdicts:
        if v["status"] not in STATUSES:
            raise SystemExit(f"Bad status {v}")
        if v["status"] == "CHANGED_AFTER_REVIEW" and v["id"] not in changes:
            raise SystemExit(f"CHANGED without logged change: {v['id']}")
        log[v["id"]] = {"id": v["id"], "status": v["status"], "note": v.get("note", ""), "reviewer": "Claude Opus 5.5 (round 006)"}
    LOG.write_text(json.dumps(sorted(log.values(), key=lambda e: e["id"]), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"review_log entries: {len(log)}")


if __name__ == "__main__":
    if sys.argv[1] == "export":
        export(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    else:
        record(sys.argv[2])
