"""Merge translation shards and validate IDs, Unicode, markup and timing tokens."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TAGS = re.compile(r"</>|</?[A-Za-z_][^<>\r\n]*>")
# All five uppercase bracket occurrences were inspected: UI labels or sounds.
PLACEHOLDERS = re.compile(r"\{\{[^{}\r\n]+\}\}|\{[^{}\r\n]+\}|(?<![0-9%])%(?:\d+\$)?[-+#0 ]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:ll|[hlLzjt])?[sdiufFeEgGxXocp]|\[(?!HIGH\]|OVERRIDDEN\]|SCREEEEECH\]|SCREEEEEEECH\])[A-Z][A-Z0-9_]+\]")
URLS = re.compile(r'https?://[^\s<>"\u201c\u201d]+')
EMAILS = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
ARABIC = re.compile(r"[\u0620-\u064a\u066e-\u06d3]")
STATES = {"TODO", "TRANSLATED", "REVIEWED", "TESTED", "FINAL"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def issues(en, ar):
    errors = []
    if not isinstance(ar, str):
        return ["Arabic value is not a string"]
    if not ar.strip() and en.strip():
        errors.append("Empty Arabic")
    for label, pattern in [("Rich-text tags", TAGS), ("Placeholders", PLACEHOLDERS)]:
        if Counter(pattern.findall(en)) != Counter(pattern.findall(ar)):
            errors.append(f"{label} differ")
    for label, pattern in [("URLs", URLS), ("Email addresses", EMAILS)]:
        if Counter(pattern.findall(en)) != Counter(pattern.findall(ar)):
            errors.append(f"{label} differ")
    for token in ["|", "^", "\r", "\n", "\t", "\\", r"\n", r"\t"]:
        if en.count(token) != ar.count(token):
            errors.append(f"Timing/format token count differs: {token!r}")
    if "\ufffd" in ar or "\0" in ar or any(0xd800 <= ord(c) <= 0xdfff for c in ar):
        errors.append("Unicode corruption or NUL")
    if any(0xfb50 <= ord(c) <= 0xfdff or 0xfe70 <= ord(c) <= 0xfeff for c in ar):
        errors.append("Presentation-form text: renderer must shape logical Unicode")
    if any(c in ar for c in "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"):
        errors.append("Directional controls require explicit review")
    for c in ar:
        if unicodedata.category(c) == "Cc" and c not in "\n\r\t":
            errors.append("Unexpected control character")
            break
    return errors


def is_technical(text, namespace=""):
    residue = PLACEHOLDERS.sub("", TAGS.sub("", text)).strip()
    return (not re.search(r"[A-Za-z]", residue) or residue in {"Dispatch", "Steam", "SDN", "XP", "HP", "EXP", "AO", "FL", "MES", "NM", "NoIcon", "Svg", "*+*+*+*Disabled_Volta_Virtu*+*+*+*", "11022 cs    |    15.79%     |   0:26     |     6096K", "- - - - - - - - - - - - - - - - - - - - v ^ x"}
            or (namespace in {"InputKeys", "FInputChord"} and bool(re.fullmatch(r"[A-Z]|F\d{1,2}|Alt|Ctrl|Shift|Cmd|Esc|Tab|Enter|NumLock|CapsLock|ScrollLock", residue)))
            or residue in {"Alt", "Enter", "Tab", "Esc", "!!!!!BRAINDEAD_REWIRED!!!!!!", "x : 24.52  y : 33.38  z : 91.01", "x :  y :  z :", "x:  y:  z:", "02-09-19XX", "SONAR.XLSX", "T---------", "°C", "°F", ".XLSX", ":DROWSSAP"}
            or bool(re.fullmatch(r"[A-HSWY][+-]?", residue))
            or bool(re.fullmatch(r"[A-Z0-9]{4,}", residue) and re.search(r"[0-9]", residue))
            or residue.startswith(("SEP [", "SSP ["))
            or bool(re.fullmatch(r"(?:https?://|[A-Za-z]:\\|@)[^\s]+", residue))
            or bool(re.fullmatch(r"(?:BuildPreview|DestroyPreview|ClickLeftMouse|NextDossierClick|\.Graph)", residue)))


def validate(write_master=True):
    records, errors, warnings, targets = [], [], [], []
    approvals_path = ROOT / "translation/VERBATIM_APPROVALS.json"
    approvals = load(approvals_path) if approvals_path.exists() else {}
    review_path = ROOT / "translation/review/review_log.json"
    review = {e["id"]: e["status"] for e in json.loads(review_path.read_text(encoding="utf-8"))} if review_path.exists() else {}
    for source in sorted((ROOT / "translation/source").glob("*.json")):
        rows = load(source)
        path = ROOT / "translation/arabic" / source.name
        translated = load(path) if path.exists() else {}
        wanted = {str(row["index"]) for row in rows}
        for extra in sorted(set(translated) - wanted):
            errors.append({"target": source.stem, "index": extra, "issues": ["Unknown translation index"]})
        for row in rows:
            row = dict(row)
            index = str(row["index"])
            if index in translated:
                row["ar"], row["status"] = translated[index], "TRANSLATED"
                if review.get(row["id"]) in ("REVIEWED_OK", "CHANGED_AFTER_REVIEW"):
                    row["status"] = "REVIEWED"  # a human-style literary pass, not a runtime test
                row_errors = issues(row["en"], row["ar"])
                if row["ar"] == row["en"]:
                    approval = approvals.get(row["id"], {})
                    if approval.get("en") == row["en"] and approval.get("reason"):
                        row["notes"] = approval["reason"]
                    elif is_technical(row["en"], row["namespace"]):
                        row["notes"] = "Preserved technical identifier, brand, placeholder, number or symbol."
                    else:
                        row_errors.append("Untranslated natural-language candidate")
                elif (not ARABIC.search(TAGS.sub("", row["ar"]))
                      and re.search(r"[A-Za-z]", PLACEHOLDERS.sub("", TAGS.sub("", row["en"])))
                      and not is_technical(row["ar"], row["namespace"])):
                    warnings.append({"id": row["id"], "issue": "No Arabic letters; review retained wording"})
                if row_errors:
                    errors.append({"id": row["id"], "index": row["index"], "issues": row_errors})
            else:
                errors.append({"id": row["id"], "index": row["index"], "issues": ["Missing Arabic"]})
            if not row["en"]:
                warnings.append({"id": row["id"], "issue": "Original English is empty"})
            records.append(row)
        targets.append({"target": source.stem, "total": len(rows),
                        "completed": sum(str(row["index"]) in translated for row in rows)})
    ids = Counter(row["id"] for row in records)
    for key, count in ids.items():
        if count > 1:
            errors.append({"id": key, "issues": ["Duplicate source identity"]})
    done = [r for r in records if r["status"] in ("TRANSLATED", "REVIEWED")]
    review_counts = Counter(review.values())
    progress = {"total": len(records), "translated": len(done),
                "arabic_changed": sum(r["ar"] != r["en"] for r in done),
                "verbatim_preserved": sum(r["ar"] == r["en"] for r in done),
                "reviewed": sum(r["status"] == "REVIEWED" for r in records),
                "review_breakdown": {k: review_counts.get(k, 0) for k in ("REVIEWED_OK", "CHANGED_AFTER_REVIEW", "NEEDS_CONTEXT", "BLOCKED")},
                "tested_in_game": 0, "final": 0,
                "game_launch_prohibited_by_user": True, "targets": targets,
                "validation_errors": len(errors), "validation_warnings": len(warnings)}
    for path, data in [("translation/progress.json", progress), ("reports/validation.json", {"errors": errors, "warnings": warnings})]:
        (ROOT / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if write_master:
        dest = ROOT / "translation/records"
        dest.mkdir(exist_ok=True)
        for target in targets:
            (dest / f"{target['target']}.json").write_text(json.dumps([r for r in records if r["target"] == target["target"]], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with (ROOT / "translation/MASTER_TRANSLATION.md").open("w", encoding="utf-8", newline="\n") as stream:
            stream.write("# Dispatch Arabic translation master\n\nEnglish originals are retained. Status TRANSLATED is not a runtime/visual acceptance result.\n\n")
            for row in records:
                stream.write(f"[ID: {row['id']}]\n\nAR:\n```text\n{row['ar']}\n```\n\nEN:\n```text\n{row['en']}\n```\n\nSource File: {row['source_file']}\n\nContext: {'; '.join(row['context'])}\n\nSpeaker: {row['speaker'] or 'Unconfirmed'}\n\nStatus: {row['status']}\n\nNotes: {row['notes']}\n\n---\n\n")
    print(json.dumps(progress, ensure_ascii=True, indent=2))
    print("Error categories:", dict(Counter(issue for error in errors for issue in error["issues"])))
    return errors


def selftest():
    assert not issues('Press <b>{KEY}</b> | Next ^thing^ %d', 'اضغط <b>{KEY}</b> | التالي ^شيء^ %d')
    assert any("Placeholders" in e for e in issues('Hello {name}', 'مرحبًا'))
    assert any("tags" in e for e in issues('<b>Hello</>', 'مرحبًا'))
    assert issues('One|Two', 'واحد')
    assert issues('X', '\ufefb')
    assert issues('X', '\u202eاختبار')
    assert not issues('^<4 slots^', '^<4 خانات^')
    assert not issues('Increase by 25% per slot', 'زيادة 25% لكل خانة')
    assert not issues('[HIGH]', '[مرتفع]')
    assert issues('https://example.com', 'https://example.org')
    assert not issues('Last {N}|plural(one=minute,other=minutes)', 'منذ {N}|plural(one=دقيقة,other=دقائق)')
    try:
        json.loads('{"1":"a","1":"b"}', object_pairs_hook=unique_object)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate IDs accepted")
    print("Markup, placeholder, timing, Unicode and duplicate-key self-checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--no-master", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        sys.exit(bool(validate(not args.no_master)))
