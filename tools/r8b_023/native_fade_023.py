"""Round 024: EXE signature evidence for the two new fade natives (Divide_FloatFloat, FClamp), read-only.

Same decoder as native_returns_019.py (UHT FFunctionParams). Output = the round-019 evidence plus the two entries, so the fade
WBP generator can fail closed before it emits a call: every candidate must be KismetMathLibrary (OuterFunc 0x285ae80, the
same OuterFunc as the already-resolved Add/Subtract/Multiply_FloatFloat) with exact float parameters and a float return.
python -X utf8 -I tools/r8b_023/native_fade_023.py <native_returns_019.json> <out.json>
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "r8b_019"))
import native_returns_019 as nr  # noqa: E402

NEW = {"KismetMathLibrary.Divide_FloatFloat": ["Float", "Float"], "KismetMathLibrary.FClamp": ["Float", "Float", "Float"]}
OUTER = "0x285ae80"


def main(src, out):
    assert hashlib.sha256(nr.EXE.read_bytes()).hexdigest() == nr.EXE_SHA, "unexpected EXE build"
    base = json.loads(Path(src).read_text(encoding="utf-8"))
    assert base["exe_sha256"] == nr.EXE_SHA
    anchors = {base["functions"][k]["candidates"][0]["outer_rva"] for k in ("KismetMathLibrary.Add_FloatFloat", "KismetMathLibrary.Subtract_FloatFloat")}
    assert anchors == {OUTER}, anchors
    img = nr.Image()
    for key, params in NEW.items():
        raw = nr.candidates(img, key.split(".")[-1])
        same = [c for c in raw if len(c["params"]) == len(params)]
        ok = bool(same) and all(c["outer_rva"] == OUTER and c["return"] == "Float" and [p["type"] for p in c["params"]] == params
                                and not any(p["out"] or p["reference"] for p in c["params"]) for c in same)
        base["functions"][key] = {"candidates": raw, "argument_counts": [[len(params), 1]], "return": "Float" if ok else "UNRESOLVED",
                                  "params": same[0]["params"] if ok else None, "evidence": "EXE_UNIQUE" if ok and len(same) == 1 else "EXE_ALL_CANDIDATES_AGREE" if ok else "UNRESOLVED",
                                  "wildcard": False}
        print("%-40s %-10s candidates=%d outer=%s" % (key, base["functions"][key]["return"], len(raw), sorted({c["outer_rva"] for c in raw})))
    base["source"] = "round-019 evidence + round-024 fade natives"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(base, indent=1) + "\n", encoding="utf-8")
    assert all(base["functions"][k]["return"] == "Float" for k in NEW), "fade native signature unresolved"


if __name__ == "__main__":
    main(*sys.argv[1:3])
