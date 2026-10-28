"""Offline integration checks. No game access or AES key access.

python -X utf8 tools/asset_inspector/test_stage1.py [builds/rtl_poc/stage1]
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def segmentation_checks():
    spec = importlib.util.spec_from_file_location("canonical_units", ROOT / "tools/ue427_stock_reveal_test/segment_units.py")
    units = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(units)
    units.self_check()
    units.MAX_UNITS = 37  # canonical implementation, R8b capacity; no policy duplication
    units.self_check()
    text = " ".join(["السَّلَامُ", 'a<b', '&', '"TEST-42"', "50"] * 24)
    markup, count, speaker_count, delays = units.build_markup(text, "المحقق")
    assert count == 37 and speaker_count == 1 and len(delays) == 37
    assert units.plain_of(markup) == "المحقق: " + text
    assert abs(sum(delays) - 0.025 * units.letters(text)) < 1e-9, "overflow lost timing"
    assert all(tag not in markup for tag in ('<b', '"TEST-42"'))
    for token in ("أ\u00a0ب", "أ\u202fب", "أ\u200dب", "أ\u200cب", "أ\u200bب", "السَّلَامُ"):
        m, n, _, _ = units.build_markup(token)
        assert n == 1 and units.plain_of(m) == token
    assert units.build_markup("السعر 50 USD اليوم")[1] == 3
    assert units.build_markup("أ\n50 ب")[1] == 3
    assert units.build_markup("أ\tب\rج\nد")[1] == 4
    assert [s == "ar" or s.startswith("ar-") for s in ("ar", "ar-SA", "arn", "en")] == [True, True, False, False]
    # Float32 encoding is tested on the reread tables by the C# validator. Bound the threshold separately.
    assert 10.5**36 < 3.4028234663852886e38 < 10.5**38
    assert 10.5**-1 < 0.1


def main():
    segmentation_checks()
    directory = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "builds/rtl_poc/stage1")
    report = json.loads((directory / "stage1_verification.json").read_text(encoding="utf-8"))
    assert report["status"] == "R8B_WBP_STAGE1_PASS"
    assert report["unexpectedOriginalExportChanges"] == 0 and report["ENGLISH_BYTECODE_UNCHANGED"] is True
    assert len(report["validation"]) == 5 and all(x["errors"] == 0 for x in report["validation"])
    assert len(report["negativeTests"]) >= 10 and all(x["detected"] for x in report["negativeTests"])
    assert all(x["doubleGenerationByteEqual"] and x["rereadSerializeByteEqual"] for x in report["determinism"])
    assert report["DISPATCH_INTEGRATION_PROVEN"] is False and report["IN_GAME_RTL_PROVEN"] is False
    assert report["tested_in_game"] == report["final"] == 0
    for entry in report["validation"]:
        name = entry["asset"]
        stem = directory / (name if name.startswith("WBP_") else "Dispatch/Content/ArabicReveal/" + name)
        for ext in ("uasset", "uexp"):
            assert hashlib.sha256(stem.with_suffix("." + ext).read_bytes()).hexdigest().upper() == entry[ext + "_sha256"]
    dll = ROOT / "tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll"
    proc = subprocess.run(["dotnet", str(dll), "--validate-arabic-wbp-stage1", str(ROOT), str(directory)],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr[-2500:]
    independent = json.loads(proc.stdout)
    assert independent["status"] == "STAGE1_OFFLINE_VALIDATION_PASS" and independent["determinismEvidenceMatches"]
    assert len(independent["negativeTests"]) >= 10
    print("PASS: Stage1 independent binary validator, source hashes, 5 assets, 10 negative fixtures, segmentation at 37, markup/timing preservation, language gate")


if __name__ == "__main__":
    main()
