"""Independent re-check of the reveal screenshots (UE ISOLATED TEST - NOT DISPATCH).

For every screenshots/lines/<id>/<layer>/ folder: each state tNNN.png must be blank at t000, and
every lit pixel must equal final.png exactly; lit pixels never disappear; the last state equals final.
The 28-px label strip at the top is ignored.

usage: python -I compare_pngs.py <RevealGate output dir>   (writes pixel_check.json there)
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

LABEL_H = 28


def load(p):
    return np.asarray(Image.open(p).convert("RGB"))[LABEL_H:].astype(np.int16)


def check(folder):
    final = load(folder / "final.png")
    states = sorted(folder.glob("t[0-9][0-9][0-9].png"))
    prev = np.zeros(final.shape[:2], bool)
    out = {"states": len(states), "start_blank": None, "lit_px_differing_from_final": 0, "px_removed": 0, "end_equals_final": None}
    for i, p in enumerate(states):
        s = load(p)
        lit = s.any(axis=2)
        out["lit_px_differing_from_final"] += int((lit & (s != final).any(axis=2)).sum())
        out["px_removed"] += int((prev & ~lit).sum())
        prev = lit
        if i == 0:
            out["start_blank"] = not lit.any()
        if i == len(states) - 1:
            out["end_equals_final"] = bool((s == final).all())
    out["pass"] = bool(out["start_blank"] and out["end_equals_final"] and out["lit_px_differing_from_final"] == 0 and out["px_removed"] == 0)
    return out


def main():
    root = Path(sys.argv[1])
    res = {f"{d.parent.name}/{d.name}": check(d) for d in sorted((root / "screenshots" / "lines").glob("*/*")) if (d / "final.png").exists()}
    (root / "pixel_check.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    bad = [k for k, v in res.items() if not v["pass"]]
    print(f"{len(res)} layers checked, {len(res) - len(bad)} pass, failing: {bad}")


if __name__ == "__main__":
    main()
