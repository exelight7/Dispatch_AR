"""Compile validated Arabic locres files into an additive, experimental text pak.

This does not implement the native ProtoAnimatedText RTL reveal fix or launch games.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

from localization import ROOT, read_locres, compile_locres, select_resource
from validate_translation import load, validate

REPAK = ROOT / "tools/repak-v0.2.3/repak.exe"
PAK_NAME = "Dispatch_AR_Texts_P.pak"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pack_verified(payload, output):
    """Roundtrip every payload byte and prove pack determinism before delivery."""
    with tempfile.TemporaryDirectory(prefix="pack-", dir=ROOT / "builds") as temp:
        temp = Path(temp)
        assert temp.resolve().is_relative_to((ROOT / "builds").resolve())
        stage = temp / "payload"
        stage.mkdir()
        for name, data in payload.items():
            parts = Path(name)
            if parts.is_absolute() or ".." in parts.parts:
                raise ValueError("Unsafe archive member")
            file = stage / parts
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
        first, second = temp / "first.pak", temp / "second.pak"
        for target in [first, second]:
            # Parallel repak packing can reorder physical file payloads.
            subprocess.run([str(REPAK), "pack", str(stage), str(target), "--version", "V11", "--quiet"],
                           env={**os.environ, "RAYON_NUM_THREADS": "1"}, check=True, capture_output=True)
        packed = first.read_bytes()
        if packed != second.read_bytes():
            raise ValueError("Package output is not deterministic")
        restored = temp / "restored"
        subprocess.run([str(REPAK), "unpack", str(first), "--output", str(restored), "--quiet"], check=True, capture_output=True)
        actual = {p.relative_to(restored).as_posix(): p.read_bytes() for p in restored.rglob("*") if p.is_file()}
        if actual != payload:
            raise ValueError("Package roundtrip changed file data or archive members")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(packed)
    return digest(packed)


LABELS = ["STATIC", "EXPERIMENTAL", "NOT_INSTALL_TESTED", "NO_RTL_FIX"]
ZIP_TIME = (1980, 1, 1, 0, 0, 0)  # fixed entry timestamps so two builds produce identical archives


def build(output_root=ROOT / "builds"):
    if validate():
        raise ValueError("Translation validation failed; no release package built")
    payload, targets = {}, []
    for source in sorted((ROOT / "translation/source").glob("*.json")):
        rows = load(source)
        translated = load(ROOT / "translation/arabic" / source.name)
        original = ROOT / "extracted" / rows[0]["source_file"]
        resource = read_locres(original.read_bytes())
        identities = {(row["namespace"], row["key"]) for row in rows}
        if len(resource["rows"]) != len(rows):
            if source.stem != "EngineRuntime":
                raise ValueError("Unexpected resource/source record count mismatch")
            resource = select_resource(resource, identities)
        if {(r["namespace"], r["key"]) for r in resource["rows"]} != identities:
            raise ValueError("Source and compiled resource identities differ")
        translations = {(row["namespace"], row["key"]): translated[str(row["index"])] for row in rows}
        compiled = compile_locres(resource, translations)
        decoded = read_locres(compiled)
        for row in decoded["rows"]:
            if row["text"] != translations[(row["namespace"], row["key"])]:
                raise ValueError("Compiled translation differs from the reviewed input mapping")
        if compile_locres(decoded, {}) != compiled:
            raise ValueError("Compiled resource is not idempotent")
        # Keep the original game's or engine plugin's localization mount path.
        name = (Path(rows[0]["source_file"]).parent.parent / "ar" / original.name).as_posix()
        payload[name] = compiled
        targets.append({"target": source.stem, "strings": len(rows), "file": name,
                        "sha256": digest(compiled), "bytes": len(compiled)})
    out = output_root / "arabic_texts_experimental"
    package_hash = pack_verified(payload, out / PAK_NAME)
    investigation = load(ROOT / "reports/investigation.json")
    manifest = {"kind": "arabic-texts-experimental", "game": "Dispatch",
        "project_version": "1.0.19512", "steam_build_id": "25637711",
        "game_executable_sha256": investigation["executable_sha256"],
        "culture": "ar", "pak_name": PAK_NAME, "pak_sha256": package_hash,
        "total_strings": sum(t["strings"] for t in targets), "targets": targets,
        "structural_validation": "PASS", "pack_roundtrip": "PASS", "deterministic_pack": "PASS",
        "runtime_test": "NOT_RUN_USER_PROHIBITED_GAME_LAUNCH",
        "rtl_progressive_reveal": "UNRESOLVED_NATIVE_PROTO_ANIMATED_TEXT",
        "english_resources_overridden": False, "production_ready": False, "labels": LABELS,
        "compatibility_sha256": digest((ROOT / "compatibility/game_build.json").read_bytes())}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    readme = """حزمة نصوص Dispatch العربية التجريبية
STATIC / EXPERIMENTAL / NOT_INSTALL_TESTED / NO_RTL_FIX

هذه ترجمة موارد النصوص المستخرجة، وليست إصدارًا نهائيًا مكتملًا من التعريب.
لم يُنفذ اختبار داخل اللعبة بناءً على طلب المستخدم.
الظهور العربي التدريجي في ProtoAnimatedText ما زال غير محلول.
لم تُدرج تجربة تعديل الواجهة العامة لأنها تغيّر الإنجليزية ولا تصلح الظهور التدريجي.

الحزمة تضيف ملفات اللغة ar فقط. لا تستبدل ملفات اللغة الإنجليزية أو الخطوط الأصلية.
التثبيت الاختياري من مجلد المشروع:
python scripts/install.py --experimental-text-only --game-root "<مجلد اللعبة>"
(أضف --dry-run للتحقق دون كتابة أي ملف)

لتحديد العربية عند التشغيل مستقبلًا: استخدم خيار التشغيل -culture=ar.
لم تتم إضافة العربية إلى قائمة اللغات داخل إعدادات اللعبة، ولم يُختبر احتفاظ اللعبة بهذا الخيار.
لا يقوم أي سكربت في هذه الحزمة بتشغيل اللعبة أو تعديل إعدادات الخصوصية أو ملفات الحفظ.
لإزالة الحزمة المثبتة: python scripts/install.py --uninstall --game-root "<مجلد اللعبة>"
يرفض المثبت أي إصدار للعبة غير Dispatch 1.0.19512 (Steam build 25637711).
"""
    (out / "README_AR.txt").write_text(readme, encoding="utf-8")
    archive = output_root / "Dispatch_AR_Texts_EXPERIMENTAL.zip"
    members = [(out / name, name) for name in [PAK_NAME, "manifest.json", "README_AR.txt"]] + [
        (ROOT / "scripts/install.py", "scripts/install.py"), (ROOT / "docs/INSTALL.md", "docs/INSTALL.md"),
        (ROOT / "compatibility/game_build.json", "compatibility/game_build.json")]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path, name in members:
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            bundle.writestr(info, path.read_bytes())
    print(f"Built {manifest['total_strings']} records; pak SHA256 {package_hash}")
    print(f"Experimental text package: {archive}")
    print("Native Arabic progressive reveal remains unresolved. Game was not launched.")


def poc():
    cases = load(ROOT / "tests/rtl_cases.json")
    source = ROOT / "extracted/Dispatch/Content/Localization/Shared/en/Shared.locres"
    resource = read_locres(source.read_bytes())
    identity = ("SettingsSubtitlePreview", "TestSubtitle")
    assert sum((r["namespace"], r["key"]) == identity for r in resource["rows"]) == 1
    reports = []
    for i, case in enumerate(cases[:3], 1):
        compiled = compile_locres(resource, {identity: case["text"]})
        after = read_locres(compiled)
        changed = [(a["namespace"], a["key"]) for a, b in zip(resource["rows"], after["rows"]) if a["text"] != b["text"]]
        assert changed == [identity]
        assert next(r["text"] for r in after["rows"] if (r["namespace"], r["key"]) == identity) == case["text"]
        payload = {"Dispatch/Content/Localization/Shared/ar/Shared.locres": compiled}
        out = ROOT / "builds/rtl_poc" / f"{i:02d}_{case['id']}.pak"
        reports.append({"case": case["id"], "pak": out.relative_to(ROOT).as_posix(),
                        "sha256": pack_verified(payload, out), "resource_and_pack_roundtrip": "PASS",
                        "in_game": "NOT_RUN", "typewriter_acceptance": "NOT_ESTABLISHED"})
    (ROOT / "reports/poc_data_checks.json").write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    print("Three data-only RTL probe packages verified; no runtime/visual acceptance result.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poc", action="store_true", help="Build data-only probes; never claim visual success")
    parser.add_argument("--output-root", type=Path, default=ROOT / "builds", help="Detached output folder (default builds/)")
    args = parser.parse_args()
    poc() if args.poc else build(args.output_root.resolve())
