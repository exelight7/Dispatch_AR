"""Aggregate every safe static check of the Arabic project into reports/STATIC_VERIFICATION.json.

python -X utf8 scripts/verify_project.py [--skip-fonts]
Never runs the game, never installs, never writes outside the workspace, never prints the AES key.
A PASS here is STATIC_PASS only; it is not an in-game result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PY = [sys.executable, "-X", "utf8"]
REQUIRED = [
    "translation/engine_scope.json", "translation/GLOSSARY.json", "translation/STYLE_GUIDE.md", "translation/VERBATIM_APPROVALS.json",
    "translation/review/review_queue.json", "translation/review/REVIEW_QUEUE.md", "translation/review/review_log.json",
    "reports/coverage/engine_classification_summary.json", "reports/coverage/othercontent_manifest_only.json",
    "reports/coverage/non_locres_text.json", "reports/coverage/NON_LOCRES_TEXT.md", "reports/coverage/image_localization.json",
    "reports/coverage/IMAGE_LOCALIZATION.md", "reports/coverage/video_localization.json", "reports/coverage/VIDEO_LOCALIZATION.md",
    "reports/arabic_activation/ARABIC_CULTURE.md", "reports/arabic_activation/requirements.json", "reports/arabic_activation/L10N_AR.md",
    "reports/fonts/FONT_READINESS.md", "reports/fonts/font_coverage.json", "reports/validation/ARABIC_UNICODE_SAFETY.md",
    "reports/build/PACKAGE_AUDIT.md", "docs/RELEASE_PLAN.md", "docs/PACKAGE_LAYOUT.md", "compatibility/game_build.json",
    "reports/rtl_research/renderer_repair/NEXT_INTEGRATION_CHECKLIST.md", "reports/rtl_research/renderer_repair/WBP_PATCH_PLAN.md",
    "reports/PROJECT_COMPLETION_MATRIX.md", "reports/project_completion_matrix.json",
    "reports/rtl_research/renderer_repair/WBP_STAGE1_RESULT.md",
    "reports/rtl_research/renderer_repair/WBP_STAGE2_BYTECODE_MAP.md",
    "reports/rtl_research/renderer_repair/R8B_PACKAGE_PLAN.md",
    "reports/rtl_research/renderer_repair/WBP_STAGE2_RESULT.md",
    "reports/rtl_research/renderer_repair/WBP_REVEAL_RESULT_011.md",
    "reports/rtl_research/renderer_repair/SCHEDULER_TIMING_011.md",
    "reports/rtl_research/renderer_repair/SCHEDULER_AUDIT_012.md",
    "reports/rtl_research/renderer_repair/WBP_CLOCK_RESULT_012.md",
    "reports/rtl_research/renderer_repair/R8B_REPAIR_019.md",
    "reports/rtl_research/renderer_repair/R8B_STYLEFIX_021.md",
]
ZIP_ALLOWED = {"Dispatch_AR_Texts_P.pak", "manifest.json", "README_AR.txt", "scripts/install.py", "docs/INSTALL.md",
               "compatibility/game_build.json"}
LABELS = ["STATIC", "EXPERIMENTAL", "NOT_INSTALL_TESTED", "NO_RTL_FIX"]


def run(args):
    proc = subprocess.run(PY + args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout + proc.stderr).strip().splitlines()[-1:] or [""]


def check(results, name, ok, detail):
    results.append({"check": name, "status": "STATIC_PASS" if ok else "FAIL", "detail": detail})


def package_audit(results):
    archive = ROOT / "builds/Dispatch_AR_Texts_EXPERIMENTAL.zip"
    pak_dir = ROOT / "builds/arabic_texts_experimental"
    if not archive.exists():
        check(results, "package present", False, "builds/Dispatch_AR_Texts_EXPERIMENTAL.zip missing")
        return
    key_file = ROOT / "tools/local_aes_key.txt"
    key = key_file.read_text(encoding="ascii").strip() if key_file.exists() else None
    needles = [bytes.fromhex(key), key.encode(), key.upper().encode(), key.encode("utf-16le")] if key else []
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        blobs = {n: z.read(n) for n in names}
        stamps = {i.date_time for i in z.infolist()}
    check(results, "zip members allow-list", names <= ZIP_ALLOWED and "Dispatch_AR_Texts_P.pak" in names, sorted(names))
    check(results, "zip timestamps normalized", stamps == {(1980, 1, 1, 0, 0, 0)}, sorted(stamps))
    check(results, "no AES key in package", key is not None and not any(n in b for b in blobs.values() for n in needles),
          "searched raw, hex, upper-hex and UTF-16 forms (key itself not printed)" if key else "local key file absent; cannot test")
    abs_path = re.compile(rb"[A-Za-z]:\\\\?(?:Users|filessss|SteamLibrary|Program Files)", re.I)
    check(results, "no absolute local paths", not any(abs_path.search(b) for b in blobs.values()), "regex drive:\\Users|filessss|SteamLibrary")
    forbidden = re.compile(r"(?i)\.exe$|pakchunk|local_aes|aes_candidates|extracted/|reports/|\.uasset$|\.uexp$|\.tmp$")
    check(results, "no forbidden members", not any(forbidden.search(n) for n in names), "EXE, original paks, AES files, extracted assets, reports, temp")
    manifest = json.loads(blobs["manifest.json"])
    pak = blobs["Dispatch_AR_Texts_P.pak"]
    check(results, "manifest labels", manifest.get("labels") == LABELS and manifest.get("production_ready") is False, manifest.get("labels"))
    check(results, "pak hash matches manifest", hashlib.sha256(pak).hexdigest() == manifest["pak_sha256"], manifest["pak_sha256"])
    check(results, "zip pak equals build folder pak", (pak_dir / "Dispatch_AR_Texts_P.pak").read_bytes() == pak, "byte compare")
    listing = subprocess.run([str(ROOT / "tools/repak-v0.2.3/repak.exe"), "list", str(pak_dir / "Dispatch_AR_Texts_P.pak")],
                             capture_output=True, text=True).stdout.split()
    check(results, "pak contains only ar locres", bool(listing) and all(re.search(r"/ar/[^/]+\.locres$", p) for p in listing),
          f"{len(listing)} entries")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fonts", action="store_true")
    args = parser.parse_args()
    results = []
    for name, cmd in [("validate_translation selftest", ["scripts/validate_translation.py", "--selftest"]),
                      ("localization selftest", ["scripts/localization.py", "selftest"]),
                      ("installer selftest", ["scripts/install.py", "--selftest"]),
                      ("locmeta round-trip selftest", ["tools/arabic_activation/locmeta.py", "selftest"]),
                      ("full translation validation", ["scripts/validate_translation.py", "--no-master"]),
                      ("translation QA (0 errors)", ["tools/translation_qa/qa.py"])]:
        code, tail = run(cmd)
        check(results, name, code == 0, tail[0][:200])
    progress = json.loads((ROOT / "translation/progress.json").read_text(encoding="utf-8"))
    code, tail = run(["tools/asset_inspector/test_stage1.py"])
    check(results, "R8b WBP Stage1 offline integration", code == 0, tail[0][:200])
    code, tail = run(["tools/asset_inspector/test_stage2.py"])
    check(results, "R8b WBP Stage2 initialization and Kismet", code == 0, tail[0][:200])
    code, tail = run(["tools/asset_inspector/test_reveal.py"])
    check(results, "R8b reveal control offline (native clock unbound)", code == 0, tail[0][:200])
    code, tail = run(["tools/asset_inspector/test_clock.py"])
    check(results, "R8b clock adapter emitted-bytecode replay vs NativeProto", code == 0, tail[0][:200])
    code, tail = run(["tools/asset_inspector/test_repair_019.py"])
    check(results, "R8b repair 019: void Build Arabic Timing ledger + clock replay + return-contract validator", code == 0, tail[0][:200])
    audit = "reports/rtl_research/renderer_repair/r8b_repair_019/"
    code, tail = run(["-I", "tools/r8b_019/frame_audit_019.py", "builds/rtl_poc/reveal_clock_012/WBP_SubtitleBlock_AR_REVEAL_CLOCK.json",
                      "builds/rtl_poc/r8b_repair_019/WBP_SubtitleBlock_AR_R8B_REPAIR_019.json", audit + "native_returns_019.json",
                      "builds/rtl_poc/reveal_clock_012/instruction_inventory.json", "builds/rtl_poc/r8b_repair_019/instruction_inventory.json",
                      "builds/rtl_poc/stage1/original_wbp_baseline.json", audit + "frame_audit_019.json"])
    check(results, "R8b repair 019 independent frame/metadata audit", code == 0, tail[0][:200])
    code, tail = run(["tools/asset_inspector/test_stylefix_021.py"])
    check(results, "R8b style fix 021: RichTextStyleGate + RowStruct RichTextStyleRow + TextStyle model/byte equality", code == 0, tail[0][:200])
    code, tail = run(["tools/asset_inspector/test_fade_023.py"])
    check(results, "R8b fade 023: emitted Fade Tick replay == round-023 model + fade validator + frame audit", code == 0, tail[0][:200])
    check(results, "record counts", progress["total"] == progress["translated"] == 12973 and progress["validation_errors"] == 0,
          {k: progress[k] for k in ("total", "translated", "arabic_changed", "verbatim_preserved", "reviewed")})
    check(results, "protected status", progress["tested_in_game"] == 0 and progress["final"] == 0, "tested_in_game=0, final=0")
    for src in sorted((ROOT / "translation/source").glob("*.json")):
        rows = json.loads(src.read_text(encoding="utf-8"))
        ar = json.loads((ROOT / "translation/arabic" / src.name).read_text(encoding="utf-8"))
        if {str(r["index"]) for r in rows} != set(ar):
            check(results, f"index parity {src.stem}", False, "source/arabic index sets differ")
    check(results, "index parity (all targets)", all(r["check"] != "index parity" for r in results), "14 targets")
    scope = json.loads((ROOT / "translation/engine_scope.json").read_text(encoding="utf-8"))
    summary = json.loads((ROOT / "reports/coverage/engine_classification_summary.json").read_text(encoding="utf-8"))
    check(results, "engine scope / audit consistency", len(scope["identities"]) == 464 and
          summary["classified_outside_scope"] + summary["selected_scope"] == summary["total_records"] == 20282,
          f"scope {len(scope['identities'])}; audit {summary['classified_outside_scope']} + {summary['selected_scope']}")
    safety = json.loads((ROOT / "reports/validation/unicode_safety.json").read_text(encoding="utf-8"))
    check(results, "Unicode safety", safety["presentation_form_codepoints"] == 0 and not any(safety["bidi_controls"].values())
          and not any(safety["zero_width"].values()), "0 presentation forms, 0 bidi/zero-width controls")
    if not args.skip_fonts:
        code, tail = run(["tools/font_analysis/coverage.py"])
        fonts = json.loads((ROOT / "reports/fonts/font_coverage.json").read_text(encoding="utf-8"))
        check(results, "font chain coverage", code == 0 and not fonts["chain_missing_glyphs"] and fonts["shaping"]["notdef_glyphs"] == 0,
              f"missing {len(fonts['chain_missing_glyphs'])}, notdef {fonts['shaping']['notdef_glyphs']}")
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            check(results, f"required file {rel}", False, "missing")
    check(results, "required files present", all(not r["check"].startswith("required file") for r in results), f"{len(REQUIRED)} files")
    for rel in ["reports/coverage/non_locres_text.json", "reports/coverage/image_localization.json", "reports/coverage/video_localization.json",
                "reports/arabic_activation/requirements.json", "compatibility/game_build.json", "reports/project_completion_matrix.json"]:
        try:
            json.loads((ROOT / rel).read_text(encoding="utf-8"))
        except Exception as error:  # report, do not abort the aggregate
            check(results, f"json parses {rel}", False, str(error))
    compat = json.loads((ROOT / "compatibility/game_build.json").read_text(encoding="utf-8"))
    check(results, "compatibility metadata", compat["supported_builds"][0]["steam_build_id"] == "25637711" and compat["contains_secrets"] is False,
          compat["supported_builds"][0]["project_version"])
    package_audit(results)
    final = json.loads((ROOT / "reports/FINAL_VERIFICATION.json").read_text(encoding="utf-8"))
    check(results, "final verification consistency", final.get("installed_into_game") is False and final.get("visual_acceptance") == "NOT_RUN",
          "installed_into_game=false, visual_acceptance=NOT_RUN")
    failed = [r for r in results if r["status"] != "STATIC_PASS"]
    report = {"overall": "STATIC_PASS" if not failed else "FAIL", "checks": len(results), "failed": len(failed),
              "meaning": "STATIC_PASS only. Not BUILD/ROUNDTRIP beyond the listed checks, not EDITOR_PASS, not IN_GAME_PASS.",
              "game_run": False, "installed": False, "results": results}
    (ROOT / "reports/STATIC_VERIFICATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in results:
        print(f"{r['status']:12} {r['check']}")
    print(f"\nOVERALL: {report['overall']} ({len(results) - len(failed)}/{len(results)})")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
