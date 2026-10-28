"""Round 022: why the Run 6 R8b reveal looks less smooth than stock Proto. Offline, read-only; never runs or touches the game.

1. Emitted-bytecode replay of the INSTALLED WBP (r8b_repair_019 JSON dump of uasset e4189ec2...) on every 50th real
   Arabic subtitle: Build Arabic Markup/Timing -> Begin Reveal -> K2_SetTimer/Arabic Clock Fired at a fixed 60 fps,
   cross-checked against the round-012 adapter model (clock_model_012.Arabic).
2. Whole corpus (adapter model): R8b word-unit visible-change cadence vs native Proto per-letter cadence
   (shipped rows: PrintLetterInterval 0.025, PrintLetterAnimationTime 0, UseAdvancedPrintIntervals false, SpaceInterval 0).
3. Fractional-threshold ramp check of the shipped opacity code (row B = 10.5^-i, tint B = 10.5^t,
   opacity = sat((B-0.1)*1.11), 8-bit sRGB vertex colour). DESIGN_INFERENCE for the next task, not in-game evidence.

usage: python -X utf8 -I tools/r8b_022/cadence_022.py <project> <out.json>
"""
import glob
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(ROOT / "tools/asset_inspector"))
import test_clock as tc   # binds clock_model_012 and segment_units (MAX_UNITS = 37)

model, ref = tc.model, tc.reference
FPS, DT = 60, 1 / 60
WBP = ROOT / "builds/rtl_poc/r8b_repair_019"
asset = json.loads((WBP / "WBP_SubtitleBlock_AR_R8B_REPAIR_019.json").read_text())
inventory = json.loads((WBP / "instruction_inventory.json").read_text())
recs = [r for p in sorted(glob.glob(str(ROOT / "translation/records/*.json"))) for r in json.load(open(p, encoding="utf-8"))]
# Speaker names were OFF in CloudSettings for Runs 5/6, so content only; italic markers are removed before markup.
subs = [s for s in (r["ar"].replace("<Italic>", "").replace("</>", "") for r in recs if r["category"] == "Dialogue/Subtitles")
        if ref.letters(s) > 0]


def run_until_finish(world, obj, finished):
    f = 0
    while not finished() and f < 20000:
        f += 1; obj.frame = f; world.tick(DT, False, 1.0)


def native_frames(n_letters):
    """Native Proto: one item per counted letter, 0.025 s each."""
    w = model.World(); nat = model.NativeProto(w, [0.025] * n_letters + [0.025], False); nat.frame = 0; nat.start(0)
    run_until_finish(w, nat, lambda: nat.finish)
    return [nat.reveal[i] for i in range(n_letters)]


def model_unit_frames(delays):
    w = model.World(); ar = model.Arabic(w, delays, False); ar.frame = 0; ar.begin(0)
    run_until_finish(w, ar, lambda: ar.finish)
    return [ar.reveal[i] for i in range(len(delays))]


def vm_unit_frames(content):
    """The installed bytecode, AWP=false (gameplay route), animation ON."""
    vm = tc.fresh(asset, inventory); line = tc.Line(vm)
    vm.run("Arabic Cancel")
    vm.run("Build Arabic Markup", (content, "")); vm.run("Build Arabic Timing", (content, ""))
    vm.state.update({"bArabicActive": True, "bArabicProtoSuppressed": True, "Animate While Paused": False})
    vm.run("Set Threshold Arabic", (vm.state["ArabicSpeakerUnits"] - 1,)); vm.run("Arabic Begin Reveal")
    line.observe()
    while not line.finish and line.frame < 20000:
        line.frame += 1; vm.engine.w.tick(DT, False, 1.0); line.observe(); line.slate_tick()
    return [line.reveal[i] for i in range(vm.state["ArabicUnitCount"])], [float(x) for x in vm.state["ArabicUnitDelays"]]


def events(frames, weights):
    ev = Counter()
    for f, w in zip(frames, weights):
        ev[f] += w
    return sorted(ev.items())


def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(q * len(xs)))]


def summarize(evs, frames_total):
    gaps = [b[0] - a[0] for ev in evs for a, b in zip(ev, ev[1:])]
    chars = [c for ev in evs for _, c in ev]
    n = sum(len(ev) for ev in evs)
    return {"visible_changes": n, "changes_per_second": round(n / (frames_total / FPS), 2),
            "share_of_frames_with_visible_change": round(n / frames_total, 3),
            "gap_frames": {"p10": pct(gaps, .1), "median": statistics.median(gaps), "mean": round(statistics.mean(gaps), 2),
                           "p90": pct(gaps, .9), "max": max(gaps), "cv": round(statistics.pstdev(gaps) / statistics.mean(gaps), 3),
                           "share_ge_10": round(sum(g >= 10 for g in gaps) / len(gaps), 3),
                           "histogram_capped_20": dict(sorted(Counter(min(g, 20) for g in gaps).items()))},
            "chars_per_change": {"mean": round(statistics.mean(chars), 2), "p90": pct(chars, .9), "max": max(chars)}}


# 1) emitted bytecode vs model on a deterministic sample
sample = subs[::50]; delay_eq = frame_eq = 0; max_diff = 0
for s in sample:
    vf, vd = vm_unit_frames(s)
    _, _, _, rd = ref.build_markup(s, "")
    delay_eq += len(vd) == len(rd) and all(abs(a - b) < 1e-6 for a, b in zip(vd, rd))
    mf = model_unit_frames(rd); frame_eq += vf == mf
    max_diff = max([max_diff] + [abs(a - b) for a, b in zip(vf, mf)])
assert delay_eq == len(sample) and max_diff <= 1, (delay_eq, max_diff)

# 2) corpus cadence
r_ev, n_ev, total, letters_per_unit, first_r, first_n, end_diff, multi, tail_gaps = [], [], 0, [], [], [], Counter(), 0, []
over37 = tail_letters = 0
for s in subs:
    _, n, _, d = ref.build_markup(s, "")
    lw = [round(x / 0.025) for x in d]   # rule 7: delay = 0.025 x letters(unit); ready(U) = its LAST letter
    _, units = ref.units_of(s)
    if len(units) > 37:
        over37 += 1; tail_letters += lw[-1]
    uf, nf = model_unit_frames(d), native_frames(sum(lw))
    letters_per_unit += lw; r_ev.append(events(uf, lw)); n_ev.append(events(nf, [1] * len(nf)))
    total += max(uf[-1], nf[-1]) + 1; end_diff[uf[-1] - nf[-1]] += 1
    first_r.append(uf[0]); first_n.append(nf[0]); multi += sum(c > 1 for c in Counter(uf).values())
    if n == 37: tail_gaps.append(uf[-1] - uf[-2])

# 3) fractional threshold ramp under the shipped opacity code (8-bit sRGB vertex colour, exact sRGB decode in the VS)
def srgb8(l):
    l = min(max(l, 0.0), 1.0); s = l * 12.92 if l <= 0.0031308 else 1.055 * l ** (1 / 2.4) - 0.055
    return int(s * 255.999)
def lin(b):
    s = b / 255; return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
opacity = lambda b_linear: min(max((lin(srgb8(b_linear)) - 0.1) * 1.11, 0.0), 1.0)
fs = [i / 4000 for i in range(4001)]
ramp = sorted({round(opacity(10.5 ** (f - 1)), 4) for f in fs})

ex = sorted(subs, key=ref.letters)[len(subs) // 2]
_, ex_n, _, ex_d = ref.build_markup(ex, ""); ex_lw = [round(x / 0.025) for x in ex_d]
result = {
    "label": "OFFLINE MODEL / emitted-bytecode replay at fixed 60 fps - not Unreal execution, not in-game timing",
    "inputs": {"wbp_json": str(WBP / "WBP_SubtitleBlock_AR_R8B_REPAIR_019.json"), "installed_wbp_uasset_sha256":
               "e4189ec226170f487ed232ebc0a4659fa559d91738a2aea6d59f892cd02b6f52", "subtitles": len(subs)},
    "emitted_bytecode_crosscheck": {"sample": len(sample), "unit_delays_equal_reference": delay_eq,
                                    "reveal_frames_equal_model": frame_eq, "max_frame_diff": max_diff,
                                    "note": "0.025 s = 1.5 frames, so every 2nd boundary is an exact frame tie; float32 tie-break moves it <= 1 frame"},
    "units": {"count": len(letters_per_unit), "letters_mean": round(statistics.mean(letters_per_unit), 2),
              "letters_median": statistics.median(letters_per_unit), "letters_p90": pct(letters_per_unit, .9),
              "letters_max": max(letters_per_unit), "lines_over_37_units": over37, "merged_tail_letters_total": tail_letters,
              "tail_gap_frames_top10": sorted(tail_gaps)[-10:]},
    "r8b_word_units": summarize(r_ev, total),
    "native_proto_letters": summarize(n_ev, total),
    "frames_revealing_more_than_one_unit": multi,
    "line_end_frame_minus_native": dict(sorted(end_diff.items())),
    "first_visible_frame": {"r8b_median": statistics.median(first_r), "r8b_p90": pct(first_r, .9),
                            "native_median": statistics.median(first_n), "native_p90": pct(first_n, .9)},
    "fractional_threshold_ramp_DESIGN_INFERENCE": {
        "next_unit_opacity_at_f": {str(f): round(opacity(10.5 ** (f - 1)), 3) for f in (0, .25, .5, .75, .999)},
        "distinct_levels": len(ramp), "max_level_step": round(max(b - a for a, b in zip(ramp, ramp[1:])), 4),
        "unit_after_next_max_opacity": max(opacity(10.5 ** (f - 2)) for f in fs),
        "revealed_unit_opacity_min": min(opacity(10.5 ** f) for f in fs)},
    "example": {"text": ex, "unit_letters": ex_lw, "r8b_changes_frame_chars": events(model_unit_frames(ex_d), ex_lw),
                "native_changes_frame_chars": events(native_frames(sum(ex_lw)), [1] * sum(ex_lw))},
}
assert multi == 0 and set(end_diff) <= {-1, 0, 1}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("R8B_CADENCE_022", json.dumps({k: result[k] for k in ("emitted_bytecode_crosscheck", "frames_revealing_more_than_one_unit",
      "line_end_frame_minus_native", "first_visible_frame")}, ensure_ascii=False))
print("r8b   ", json.dumps(result["r8b_word_units"]))
print("native", json.dumps(result["native_proto_letters"]))
