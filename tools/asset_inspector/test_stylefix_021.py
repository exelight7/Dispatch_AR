"""Round 021: RichTextStyleGate validator + independent byte check on the rebuilt DT_AR tables.

Runs --validate-arabic-stylefix-021 (RowStruct, rows, exact transformation, TextStyle equality, gate on the 019 WBP, Run 5 tables
rejected, negative fixtures), then tools/r8b_021/textstyle_bytes_021.py on the artifact (must pass) and on the round-019 tables
(must fail). python -X utf8 tools/asset_inspector/test_stylefix_021.py [artifact dir]
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = "builds/rtl_poc/r8b_stylefix_021"
REQUIRED_FIXTURES = {"Run 5 tables (round-019 DT_AR, ProtoRichTextStyleRow) -> reject", "ProtoRichTextStyleRow table -> reject",
                     "TableRowBase table -> reject", "unresolved RowStruct (unknown native struct) -> reject",
                     "correct RichTextStyleRow tables (round 021) -> accept"}


def main():
    directory = ROOT / (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR)
    proc = subprocess.run(["dotnet", str(ROOT / "tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll"), "--validate-arabic-stylefix-021", str(ROOT), str(directory)],
                          capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr[-2500:]
    result = json.loads(proc.stdout)
    assert result["status"] == "R8B_STYLEFIX_021_PASS" and result["textstyle_equal_rows"] == 152 and result["run5_tables_rejected"] == 14
    fixtures = {x["fixture"]: x for x in result["negative_tests"]}
    assert REQUIRED_FIXTURES <= set(fixtures) and all(x["expected"] == x["result"] for x in fixtures.values())
    checker = [sys.executable, "-X", "utf8", "-I", str(ROOT / "tools/r8b_021/textstyle_bytes_021.py")]
    with tempfile.TemporaryDirectory() as tmp:
        good = subprocess.run(checker + [str(directory), str(Path(tmp) / "good.json")], capture_output=True, text=True)
        bad = subprocess.run(checker + [str(ROOT / "builds/rtl_poc/stage1/Dispatch/Content/ArabicReveal"), str(Path(tmp) / "bad.json")], capture_output=True, text=True)
    assert good.returncode == 0 and good.stdout.startswith("TEXTSTYLE_BYTES_IDENTICAL"), good.stdout + good.stderr
    assert bad.returncode == 1 and bad.stdout.startswith("FAIL"), "byte check accepted the Run 5 tables"
    print(f"PASS: RichTextStyleGate + 4 tables RowStruct {result['row_struct']}, TextStyle 152/152 (model and bytes), Run 5 tables rejected, {len(fixtures)} fixtures")


if __name__ == "__main__":
    main()
