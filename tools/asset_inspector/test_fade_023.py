"""Round 024: replay the EMITTED fade WBP bytecode against the round-023 fade model (tools/r8b_023/fade_model_023.py, frozen).

Each block runs three ways in lockstep: the emitted fade VM (reread package JSON, test_stage2.VM + the clock_model_012 World
bound to K2_SetTimer/GetTimeSeconds), the round-023 model Block, and (corpus) the emitted round-019 VM = the Run 6 WBP.
Required: tint B frame-identical to the model on every 50th subtitle and on all 3,000 lifecycle seeds; integer boundaries and
final threshold identical to round 019; markup/timing/SetText path unchanged; then --validate-arabic-fade-023, an independent
frame audit (frame_audit_019.Asset) and an EXE re-derivation of every native signature.
Offline evaluator only; not Unreal execution, not in game.
python -X utf8 tools/asset_inspector/test_fade_023.py [builds/rtl_poc/r8b_fade_023]
"""
import hashlib
import importlib.util
import json
import math
import random
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import test_clock as tc
from test_stage2 import VM, ROOT, float32

NAME = "WBP_SubtitleBlock_AR_R8B_FADE_023"
DEFAULT_DIR = "builds/rtl_poc/r8b_fade_023"
OLD_DIR, OLD_NAME = ROOT / "builds/rtl_poc/r8b_repair_019", "WBP_SubtitleBlock_AR_R8B_REPAIR_019"
MODEL = ROOT / "tools/r8b_023/fade_model_023.py"
MODEL_SHA = "65d5b18ef8209288981871ee2f52c6f06c647c15933b446dab4016a2cf3fdf54"   # report_023
NATIVES = ROOT / "reports/rtl_research/renderer_repair/r8b_fade_023/native_returns_023.json"
STYLEFIX = ROOT / "builds/rtl_poc/r8b_stylefix_021"
BORDERS, RETAINERS = ("ArabicForegroundBorder", "ArabicShadowBorder"), ("ArabicShadowRetainerHorizontal", "ArabicShadowRetainerVertical")
TEXT_EFFECTS = {"SetText", "SetTextStyleSet", "SetVisibility", "SetRetainRendering", "SetTextWrapAt"}


def load_model():
    """The round-023 model's definitions (everything before its corpus run), executed unchanged from the frozen file."""
    src = MODEL.read_text(encoding="utf-8")
    assert hashlib.sha256(MODEL.read_bytes()).hexdigest() == MODEL_SHA, "round-023 model changed"
    ns, argv = {"__name__": "fade_model_023", "__file__": str(MODEL)}, sys.argv
    sys.argv = [str(MODEL), str(ROOT), "unused.json"]
    try: exec(compile(src[:src.index("# ---------------- 1)")], str(MODEL), "exec"), ns)
    finally: sys.argv = argv
    return SimpleNamespace(**ns)


M = load_model()


class FadeVM(VM):
    fade_writes = 0

    def run(self, name, args=()):
        if name != "Arabic Fade Tick": return super().run(name, args)
        k, e = len(self.calls_with_targets), len(self.effects); r = super().run(name, args)
        self.fade_writes += sum(c[0] == "SetContentColorAndOpacity" for c in self.calls_with_targets[k:]) // 2
        assert {x[0] for x in self.effects[e:]} <= {"SetContentColorAndOpacity", "RequestRender"}, "Fade Tick effect outside tint/RequestRender"
        return r

    def native(self, index, args):
        name = self.asset["Imports"][-index - 1]["ObjectName"]
        if name == "Divide_FloatFloat": return 0.0 if args[1] == 0 else float32(args[0] / args[1])   # UKismetMathLibrary: B == 0 -> 0
        if name == "FClamp": x, lo, hi = args; return float32(lo if x < lo else x if x < hi else hi)  # FMath::Clamp
        return super().native(index, args)


def fresh(asset, inventory, cls=FadeVM):
    vm = cls(asset, inventory); vm.engine = tc.Engine(vm); vm.frame = 0; vm.finishes = []
    vm.on_finish = lambda: vm.finishes.append(vm.frame); return vm


def begin(vm, text, awp=False, animate=True):
    """Set Displayed Line's Arabic reveal sequence (as test_clock.text): Cancel, markup, timing, Set Threshold, Begin, Finish if off."""
    vm.run("Arabic Cancel")
    vm.run("Build Arabic Markup", (text, "")); vm.run("Build Arabic Timing", (text, ""))
    vm.state.update({"bArabicActive": True, "bArabicProtoSuppressed": True, "Animate While Paused": awp})
    vm.run("Set Threshold Arabic", (vm.state["ArabicSpeakerUnits"] - 1,)); vm.run("Arabic Begin Reveal")
    if not animate: vm.run("Arabic Finish", (True,))


def tints(vm, since=0):
    out = {}
    for name, target, args in vm.calls_with_targets[since:]:
        if name == "SetContentColorAndOpacity": out[target] = args[0]
    return out


class Block:
    """Emitted fade VM (+ optional round-019 VM) mirrored frame by frame against one round-023 model Block."""
    def __init__(self, env, text, awp=False, old=False):
        self.env, self.text, self.awp = env, text, awp
        _, self.n, _, ref = M.ref.build_markup(text, "")
        # The model is fed the emitted float32 delay ledger (Build Arabic Timing, unchanged since round 019). It equals the
        # canonical segmenter's 0.025*N to float32 rounding; 716/7488 lines differ in the last bit of some delay.
        env.ledger.run("Arabic Cancel"); env.ledger.run("Build Arabic Timing", (text, "")); self.d = list(env.ledger.state["ArabicUnitDelays"])
        assert len(self.d) == self.n and all(abs(x - y) <= 1e-6 * max(1.0, y) for x, y in zip(self.d, ref)), "ledger != canonical segmenter"
        self.blk = M.Block(M.model.World(), self.d, awp)
        self.vm = fresh(env.asset, env.inventory)
        self.old = fresh(env.old_asset, env.old_inventory, VM) if old else None
        self.tint = {b: (1.0, 1.0, 0.0, 1.0) for b in BORDERS}; self.calls = 0
        self.ck = Counter(); self.prev_op = None; self.prev_t = -2; self.complete = None; self.vm_reveal = {}; self.old_reveal = {}

    def vms(self): return [self.vm] + ([self.old] if self.old else [])

    def pretick(self, dt):
        for w in [self.blk.w] + [v.engine.w for v in self.vms()]: w.tick(dt, False, 1.0)

    def start(self, animate=True):
        for v in self.vms(): begin(v, self.text, self.awp, animate)
        assert [float32(x) for x in self.vm.state["ArabicUnitDelays"]] == [float(x) for x in self.blk.ar.d], "emitted delays != model delays"
        assert (self.vm.state["ArabicUnitCount"], self.vm.state["ArabicSpeakerUnits"]) == (self.n, 0)
        # Text/style/visibility setup belongs to the line start; from here on only tint and RequestRender are allowed.
        self.tint.update(tints(self.vm)); self.calls = len(self.vm.calls_with_targets)

    def frame(self, f, dt=None, paused=False, skip=False, cancel=False):
        """One frame after the model already ran it (drive callback): world tick, events, Slate Tick."""
        for v in self.vms():
            v.frame = f
            if f > 0: v.engine.w.tick(dt, paused, 1.0)
            if skip: v.run("Arabic Skip")
            if cancel: v.run("Arabic Cancel")
        # Skip/Cancel are line events (Cancel collapses the Arabic widgets, unchanged since round 011), not reveal-time work.
        self.tint.update(tints(self.vm, self.calls)); self.calls = len(self.vm.calls_with_targets)
        inactive, before = not self.vm.state["bArabicActive"] or self.vm.state["ArabicFinished"], self.vm.fade_writes
        for v in self.vms():
            mark = len(v.effects); v.run("Tick", (None, math.nan))
            # Tick = Arabic Paused Clock (AWP may step and finish: Broadcast, unchanged since round 012) + Arabic Fade Tick (tint only).
            assert {e[0] for e in v.effects[mark:]} <= {"SetContentColorAndOpacity", "RequestRender", "Broadcast"}
        self.ck["fade_writes_while_finished_or_inactive"] += inactive and self.vm.fade_writes != before
        self.check(f)

    def check(self, f):
        vm, blk, ck = self.vm, self.blk, self.ck
        new = vm.calls_with_targets[self.calls:]; self.calls = len(vm.calls_with_targets)
        ck["text_or_layout_effects_after_begin"] += sum(1 for c in new if c[0] in TEXT_EFFECTS)
        sets = Counter(c[1] for c in new if c[0] == "SetContentColorAndOpacity"); renders = Counter(c[1] for c in new if c[0] == "RequestRender")
        ck["unpaired_tint_or_render"] += not (sets[BORDERS[0]] == sets[BORDERS[1]] == renders[RETAINERS[0]] == renders[RETAINERS[1]])
        self.tint.update(tints(vm, self.calls - len(new)))
        blues = {self.tint[b][2] for b in BORDERS}
        ck["foreground_shadow_desync"] += len(blues) != 1
        blue = self.tint[BORDERS[0]][2]
        ck["frames"] += 1
        ck["blue_mismatch"] += blue != float(blk.blue)
        ck["alpha_not_1"] += any(self.tint[b][3] != 1.0 or self.tint[b][:2] != (1.0, 1.0) for b in BORDERS)
        t = vm.state["ArabicThreshold"]; cur = vm.state["ArabicCurrentUnit"]
        ck["threshold_mismatch_model"] += (vm.state["bArabicActive"] or vm.state["ArabicFinished"]) and cur != blk.ar.cur   # model cancel() keeps cur
        if self.old is not None:
            ck["threshold_mismatch_019"] += (t, cur) != (self.old.state["ArabicThreshold"], self.old.state["ArabicCurrentUnit"])
            for i in range(self.old.state["ArabicCurrentUnit"] + 1): self.old_reveal.setdefault(i, f)
        for i in range(cur + 1): self.vm_reveal.setdefault(i, f)
        op = M.unit_opacity(np.float32(blue), self.n)
        if vm.state["bArabicActive"]:
            ck["threshold_regress"] += t < self.prev_t
            ck["ghost_T2"] += int(np.any(op[t + 2:] > 0))
            ck["revealed_not_full"] += int(np.any(op[:t + 1] < M.FULL[True]))
            if self.prev_op is not None:
                ck["opacity_regress"] += int(np.any(op < self.prev_op - 1e-12)); ck["changed_frames"] += int(np.any(op != self.prev_op))
            self.prev_t = t
        if self.complete is None and np.all(op >= M.FULL[True]): self.complete = f
        self.prev_op = op


def drive(b, dt_fn=lambda f: M.DT, events=None):
    """The model's own drive(); the emitted VMs run the same frame inside its callback (same dt, pause, skip, cancel)."""
    events = events or {}; seen = {}
    def dt(f): seen[f] = dt_fn(f); return seen[f]
    def cb(f, t, alpha):
        if f == 0: b.start(); b.frame(0); return
        b.frame(f, seen[f], events.get("paused", lambda f: False)(f), f in events.get("skip", ()), f in events.get("cancel", ()))
    return M.drive(b.blk, cb, dt_fn=dt, events=events)


class Env:
    def __init__(self, directory):
        self.asset = json.loads((directory / (NAME + ".json")).read_text(encoding="utf-8"))
        self.inventory = json.loads((directory / "instruction_inventory.json").read_text(encoding="utf-8"))
        self.old_asset = json.loads((OLD_DIR / (OLD_NAME + ".json")).read_text(encoding="utf-8"))
        self.old_inventory = json.loads((OLD_DIR / "instruction_inventory.json").read_text(encoding="utf-8"))
        self.ledger = fresh(self.asset, self.inventory)


def corpus(env):
    lines = M.subs[::50]; tot = Counter(); end = Counter(); per_line = []
    for s in lines:
        b = Block(env, s, old=True); drive(b)
        ck = b.ck; tot.update(ck)
        lw = [round(x / 0.025) for x in b.d]; native = M.native_frames(sum(lw))
        assert b.vm_reveal == b.old_reveal and b.vm.finishes == b.old.finishes and len(b.vm.finishes) == 1, (s, "integer boundaries differ from round 019")
        assert {k: v for k, v in b.vm_reveal.items()} == {i: b.blk.ar.reveal[i] for i in range(b.n)}
        assert b.vm.state["ArabicThreshold"] == b.old.state["ArabicThreshold"] == b.n - 1, "final threshold changed"
        assert b.complete is not None; end[b.complete - native[-1]] += 1
        assert b.vm.engine.armed() is False and b.vm.state["ArabicClockRemainder"] == -1
        assert b.vm.fade_writes == b.blk.fade_writes, (s, b.vm.fade_writes, b.blk.fade_writes)
        tot["fade_tick_writes"] += b.vm.fade_writes
        per_line.append(ck["changed_frames"] / max(1, ck["frames"]))
    bad = {k: tot[k] for k in ("blue_mismatch", "threshold_mismatch_model", "threshold_mismatch_019", "foreground_shadow_desync", "alpha_not_1", "unpaired_tint_or_render",
                               "threshold_regress", "opacity_regress", "ghost_T2", "revealed_not_full", "text_or_layout_effects_after_begin", "fade_writes_while_finished_or_inactive")}
    assert not any(bad.values()), bad
    assert set(end) <= {-1, 0, 1}, end
    return {"lines": len(lines), "selection": "every 50th of %d subtitles (fade_model_023 order)" % len(M.subs), "fps": 60, "frames": tot["frames"],
            "blue_frame_identical_to_model": tot["frames"] - tot["blue_mismatch"], "fade_tick_writes": tot["fade_tick_writes"],
            "changed_frame_share": round(tot["changed_frames"] / tot["frames"], 4), "completion_minus_native_frames": dict(sorted(end.items())),
            "integer_boundaries_identical_to_round_019": True, "final_threshold_identical": True, "violations": bad}


def lifecycle(env):
    """fade_model_023's lifecycle loop (same seed 23, same draws) with the emitted VM mirrored on every line."""
    rng = random.Random(23); life = Counter(); total = Counter(); model_artifacts = 0
    for i in range(3000):
        s = rng.choice(M.subs); awp = i % 5 == 0
        b = Block(env, s, awp)
        for _ in range(rng.randint(0, 50)): b.pretick(rng.uniform(1 / 144, 1 / 20))
        pause_on, pause_len = rng.randint(1, 60), rng.randint(5, 90)
        skip = {rng.randint(1, 120)} if rng.random() < 0.3 else set()
        cancel = {rng.randint(1, 120)} if rng.random() < 0.2 else set()
        if rng.random() < 0.1: skip = {0}
        if 0 in skip:   # animation disabled: Set Displayed Line -> Arabic Finish(True) before any Tick
            b.blk.set_threshold(-1); b.blk.ar.frame = 0; b.blk.ar.begin(0); b.blk.ar.finish_(True); b.blk.set_threshold(b.n - 1)
            b.start(animate=False); k = len(b.vm.calls_with_targets); b.vm.run("Tick", (None, math.nan))
            assert b.blk.fade_tick() is None and not b.vm.calls_with_targets[k:], "fade write with animation disabled"
            blue = tints(b.vm)[BORDERS[0]][2]
            assert blue == float(b.blk.blue) and np.all(M.unit_opacity(np.float32(blue), b.n) >= M.FULL[True])
            life["anim_off"] += 1; life["anim_off_full_now"] += 1; continue
        late_skip = bool(skip and cancel and min(skip) > min(cancel))   # model calls set_threshold(n-1) on skip even after a cancel
        drive(b, dt_fn=lambda f: rng.uniform(1 / 144, 1 / 25), events={"paused": lambda f: pause_on <= f < pause_on + pause_len, "skip": skip, "cancel": cancel})
        if late_skip and b.ck["blue_mismatch"]:
            model_artifacts += 1; b.ck["blue_mismatch"] = 0
        total.update(b.ck); total["fade_tick_writes"] += b.vm.fade_writes
        life["lines"] += 1; life["cancelled"] += bool(cancel); life["skipped"] += bool(skip); life["awp"] += awp
        life["finish_broadcasts_gt1"] += len(b.vm.finishes) > 1
        end = M.unit_opacity(np.float32(b.tint[BORDERS[0]][2]), b.n)
        life["finished_not_full"] += b.vm.state["ArabicFinished"] and not np.all(end >= M.FULL[True])
        life["cancelled_not_hidden"] += not b.vm.state["bArabicActive"] and not b.vm.state["ArabicFinished"] and bool(np.any(end > 0))
        if awp: assert b.vm.engine.set_calls == 0, "AWP=true started a world timer"
    bad = {k: total[k] for k in ("blue_mismatch", "threshold_mismatch_model", "foreground_shadow_desync", "alpha_not_1", "unpaired_tint_or_render",
                                 "threshold_regress", "opacity_regress", "ghost_T2", "revealed_not_full", "text_or_layout_effects_after_begin",
                                 "fade_writes_while_finished_or_inactive")}
    bad.update({k: life[k] for k in ("finish_broadcasts_gt1", "finished_not_full", "cancelled_not_hidden")})
    assert not any(bad.values()), (bad, model_artifacts)
    ref = json.loads((ROOT / "reports/rtl_research/renderer_repair/run7_023/fade_model_023.json").read_text(encoding="utf-8"))["lifecycle"]
    assert all(life[k] == ref[k] for k in ("lines", "cancelled", "skipped", "awp", "anim_off")), (dict(life), ref)   # same seeds as round 023
    return {"lines": 3000, "animated": life["lines"], "cancelled": life["cancelled"], "skipped": life["skipped"], "awp_true": life["awp"], "animation_off": life["anim_off"],
            "fps": "random 25-144 per frame", "pause_windows": True, "frames": total["frames"], "blue_frame_identical_to_model": total["frames"] - total["blue_mismatch"],
            "fade_tick_writes": total["fade_tick_writes"], "model_only_skip_after_cancel_lines_excluded": model_artifacts, "violations": bad,
            "draws_identical_to_round_023": True}


def lifecycle_cases(env):
    cases = []; text = max(M.subs[:200], key=M.ref.letters)
    # pause: the fade freezes (no tint write), threshold does not move, resume continues where it stopped
    b = Block(env, text, old=True); paused = lambda f: 10 <= f < 70; writes = {}
    def dtp(f): return M.DT
    drive(b, dtp, {"paused": paused})
    assert not b.ck["blue_mismatch"] and b.vm_reveal == b.old_reveal
    b2 = Block(env, text); log = []
    orig = b2.check
    def check(f): orig(f); log.append((f, b2.vm.fade_writes, b2.vm.state["ArabicThreshold"], b2.tint[BORDERS[0]][2]))
    b2.check = check; drive(b2, dtp, {"paused": paused})
    during = [x for x in log if 10 <= x[0] < 70]
    assert during[-1][1] == during[0][1] and len({x[2] for x in during}) == 1 and len({x[3] for x in during}) == 1, "fade or threshold moved while paused"
    assert log[75][1] > log[69][1], "fade did not resume"
    cases.append("pause 60 frames: 0 fade writes, threshold frozen, tint frozen, resumes; boundaries == round 019")
    # skip mid-word: Finish(True) shows everything at once, no later fade write
    b = Block(env, text); drive(b, events={"skip": {12}})
    assert b.vm.state["ArabicFinished"] and b.complete == 12 and not b.ck["blue_mismatch"]
    cases.append("skip mid-fade: full line on the skip frame, Fade Tick guarded afterwards")
    # cancel / pool reuse with a second line in the same block; the stale line never writes
    b = Block(env, text); b.vm.frame = 0; b.start()
    for f in range(1, 15): b.vm.engine.w.tick(M.DT, False, 1.0); b.vm.run("Tick", (None, math.nan))
    assert b.vm.fade_writes > 0
    b.vm.run("Arabic Cancel"); k = len(b.vm.calls_with_targets)
    assert b.vm.state["ArabicThreshold"] == -1 and b.vm.state["ArabicFadeBase"] == float32(1 / 10.5) and b.vm.state["ArabicLastBlue"] == 0.0 and b.vm.state["ArabicClockRemainder"] == -1
    for f in range(30): b.vm.engine.w.tick(M.DT, False, 1.0); b.vm.run("Tick", (None, math.nan))
    assert not b.vm.calls_with_targets[k:], "stale Fade Tick write after cancel"
    begin(b.vm, M.subs[7]); k = len(b.vm.calls_with_targets)
    b.vm.run("Tick", (None, math.nan)); assert b.vm.calls_with_targets[k:], "reused block does not fade"
    cases.append("cancel: threshold -1, FadeBase 1/10.5, LastBlue 0, no stale write; pool reuse fades the new line")
    # Stop Displaying Line during a fade
    b = Block(env, text); b.start()
    for f in range(10): b.vm.engine.w.tick(M.DT, False, 1.0); b.vm.run("Tick", (None, math.nan))
    b.vm.run("Stop Displaying Line"); k = len(b.vm.calls_with_targets)
    for f in range(30): b.vm.engine.w.tick(M.DT, False, 1.0); b.vm.run("Tick", (None, math.nan))
    assert not b.vm.calls_with_targets[k:] and b.vm.state["ArabicThreshold"] == -1 and not b.vm.state["bArabicActive"]
    cases.append("Stop Displaying Line: fade stops, hidden threshold")
    # English / inactive block: Tick is a no-op
    for awp in (False, True):
        vm = fresh(env.asset, env.inventory); vm.run("Arabic Cancel"); vm.state["Animate While Paused"] = awp; vm.effects.clear()
        before = json.dumps(vm.state, sort_keys=True, default=str); vm.run("Tick", (None, math.nan))
        assert json.dumps(vm.state, sort_keys=True, default=str) == before and not vm.effects and vm.engine.set_calls == 0
    cases.append("English/inactive Tick: no state change, no effect")
    # finish idempotent and no write after normal completion
    b = Block(env, M.subs[50]); drive(b)
    k = len(b.vm.calls_with_targets)
    for f in range(100): b.vm.engine.w.tick(M.DT, False, 1.0); b.vm.run("Tick", (None, math.nan))
    b.vm.run("Arabic Finish", (False,))
    assert not b.vm.calls_with_targets[k:] and len(b.vm.finishes) == 1
    cases.append("after normal completion: 100 Ticks + Finish again -> 0 writes, one broadcast")
    return cases


def thresholds(env):
    """Integer Set Threshold Arabic: tint/render effects identical to round 019 for every T; fade state recorded."""
    new, old = fresh(env.asset, env.inventory), fresh(env.old_asset, env.old_inventory, VM)
    for t in [-1] + list(range(37)) + [37, 99]:
        new.effects.clear(); old.effects.clear(); new.run("Set Threshold Arabic", (t,)); old.run("Set Threshold Arabic", (t,))
        assert new.effects == old.effects and new.state["ArabicThreshold"] == old.state["ArabicThreshold"]
        blue = 0.0 if t < 0 else float32(10.5 ** min(t, 36))
        assert [a[0] for n, a in new.effects if n == "SetContentColorAndOpacity"] == [(1.0, 1.0, blue, 1.0)] * 2
        assert new.state["ArabicFadeBase"] == (float32(1 / 10.5) if t < 0 else blue) and new.state["ArabicLastBlue"] == blue
    return 40


def rtl_invariants(env):
    fixtures = [("مرحبا (TEST-42) بالعالم", "المحقق"), ("السعر 50 USD اليوم", ""), ("أ\n50 ب", ""), ('a<b & "c"', ""), (" ".join(["كلمة"] * 200), "المحقق"),
                ("السَّلَامُ", ""), ("", ""), ("  أ", "المحقق"), ("مرحبا 😀 50 اليوم", "اسم")] + [(s, "") for s in M.subs[::25]]
    new, old = fresh(env.asset, env.inventory), fresh(env.old_asset, env.old_inventory, VM)
    for content, speaker in fixtures:
        for v in (new, old): v.run("Arabic Cancel")
        m1, m0 = new.run("Build Arabic Markup", (content, speaker)), old.run("Build Arabic Markup", (content, speaker))
        new.run("Build Arabic Timing", (content, speaker)); old.run("Build Arabic Timing", (content, speaker))
        assert m1 == m0 and m1.encode("utf-16-le", "surrogatepass").decode("utf-16-le") == M.ref.build_markup(content, speaker)[0], (content, speaker)
        for k in ("ArabicUnitCount", "ArabicSpeakerUnits", "ArabicUnitDelays"): assert new.state[k] == old.state[k], k
    same = ["Build Arabic Markup", "Build Arabic Timing", "AR Timing Characters", "AR Is Combining Code", "Format As Arabic Plain", "AR Escape", "AR Is Separator", "AR Is Letter Code",
            "Set Displayed Line", "Stop Displaying Line", "Arabic Apply Style", "Arabic Apply Wrap", "Arabic Step", "Arabic Advance Budget", "Arabic Begin Reveal", "Arabic Arm Clock",
            "Arabic Clock Fired", "Arabic Paused Clock", "Arabic Finish", "Arabic Cancel", "Arabic Skip"]
    by = lambda a, n: next(e for e in a["Exports"] if e["ObjectName"] == n)
    for n in same: assert all(by(env.asset, n)[k] == by(env.old_asset, n)[k] for k in ("ScriptBytecode", "LoadedProperties", "FunctionFlags")), n
    tables = {}
    manifest = json.loads((STYLEFIX / "manifest.json").read_text(encoding="utf-8"))["assets"]
    for f, sha in manifest.items(): tables[f] = hashlib.sha256((STYLEFIX / f).read_bytes()).hexdigest(); assert tables[f] == sha, f
    return {"markup_fixtures": len(fixtures), "markup_unit_count_speaker_delays_identical_to_round_019": True,
            "functions_bytecode_identical_to_round_019": same, "SetText_payload": "Set Displayed Line unchanged: SetText(Conv_StringToText(Build Arabic Markup)) on both rich texts",
            "dt_ar_tables_round_021_sha256": tables}


def frame_audit(env, directory):
    spec = importlib.util.spec_from_file_location("frame_audit_019", ROOT / "tools/r8b_019/frame_audit_019.py")
    fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)
    natives = json.loads(NATIVES.read_text(encoding="utf-8"))
    A, B = fa.Asset(directory / (NAME + ".json")), fa.Asset(OLD_DIR / (OLD_NAME + ".json"))
    sites = A.call_sites(natives); invalid = [s for s in sites if s["verdict"] != "FRAME_LAYOUT_VALID"]
    assert not invalid, invalid[:5]
    fade = next(i for i, e in A.funcs.items() if e["ObjectName"] == "Arabic Fade Tick"); lay = A.layout(A.E[fade - 1])
    assert (lay["PropertiesSize"], lay["ParmsSize"], lay["NumParms"], lay["ReturnValueOffset"]) == (24, 0, 0, "MAX_uint16")
    # Fade-touched functions: every property ElementSize equals its runtime size. Elsewhere the only mismatches are the 6 shipped
    # delegate locals (audit size table 16, serialized 20), identical in round 019.
    touched = [f for f, e in A.funcs.items() if e["ObjectName"] in ("Arabic Fade Tick", "Set Threshold Arabic", "Tick")]
    assert all(p["ElementSize"] == p["runtimeSize"] for f in touched for p in A.layout(A.E[f - 1])["properties"] if p["type"] != "StructProperty")
    mism = lambda X: [(X.E[f - 1]["ObjectName"], p["name"]) for f in X.funcs for p in X.layout(X.E[f - 1])["properties"] if p["type"] != "StructProperty" and p["ElementSize"] != p["runtimeSize"]]
    assert mism(A) == mism(B) and all(n.startswith("K2Node_CreateDelegate") for _, n in mism(A))
    changed = [A.E[f - 1]["ObjectName"] for f in B.funcs if any(A.E[f - 1].get(k) != B.E[f - 1].get(k) for k in ("ScriptBytecode", "LoadedProperties", "FunctionFlags"))]
    assert changed == ["Set Threshold Arabic", "Tick"], changed
    for f in B.funcs: assert A.layout(A.E[f - 1])["PropertiesSize"] == B.layout(B.E[f - 1])["PropertiesSize"]
    fade_sites = [s for s in sites if s["caller"] == "Arabic Fade Tick"]
    return {"call_sites": len(sites), "invalid": 0, "statement_level": sum(s["resultStorage"] == "VM_SCRATCH_UNCONSTRUCTED" for s in sites),
            "fade_tick_layout": {k: lay[k] for k in ("PropertiesSize", "ParmsSize", "NumParms", "ReturnValueOffset")},
            "functions_changed_vs_019": changed, "layouts_unchanged_vs_019": True,
            "fade_tick_call_sites": [{k: s[k] for k in ("instruction", "opcode", "callee", "return", "resultStorage", "verdict")} for s in fade_sites]}


def native_cross_check(directory):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "n.json"
        r = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "tools/r8b_019/native_returns_019.py"), str(directory / (NAME + ".json")),
                            str(ROOT / "builds/rtl_poc/stage1/original_wbp_baseline.json"), str(out)], capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stderr[-2000:]
        fresh_ = json.loads(out.read_text(encoding="utf-8"))["functions"]
    evidence = json.loads(NATIVES.read_text(encoding="utf-8"))["functions"]
    for k, v in fresh_.items():
        assert v["return"] != "UNRESOLVED" and (v["return"], v["params"]) == (evidence[k]["return"], evidence[k]["params"]), k
    return {"natives": len(fresh_), "unresolved": 0, "matches_native_returns_023": True,
            "fade": {k: fresh_[k]["candidates"][0]["outer_rva"] + " " + fresh_[k]["evidence"] for k in ("KismetMathLibrary.Divide_FloatFloat", "KismetMathLibrary.FClamp")}}


def validator(directory):
    proc = subprocess.run(["dotnet", str(ROOT / "tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll"), "--validate-arabic-fade-023", str(ROOT), str(directory)],
                          capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr[-2500:]
    r = json.loads(proc.stdout); names = {x["fixture"] for x in r["negative_tests"]}
    required = {"Fade Tick calls SetText", "Fade Tick calls SetTextStyleSet", "Fade Tick writes ArabicCurrentUnit", "Fade Tick writes ArabicThreshold", "Fade Tick calls K2_SetTimer",
                "Remainder guard missing", "slope >= 9.5", "only one Border updated", "only one shadow retainer refreshed", "Fade Tick uses InDeltaTime", "Fade Tick broadcasts finish",
                "Fade Tick modifies unit arrays", "Fade Tick modifies markup", "float native signature unresolved (FClamp evidence absent)"}
    assert r["status"] == "R8B_FADE_023_PASS" and r["errors"] == 0 and r["RichTextStyleGate_bindings"] == 14 and r["return_contract_invalid"] == 0
    assert required <= names, required - names
    assert all(x["detected"] == x["expected_detection"] for x in r["return_contract_fixtures"])
    report = json.loads((directory / "validation.json").read_text(encoding="utf-8"))
    assert report["deterministic"] and report["roundtrip"] and report["unexpected_changes"] == 0 and report["tested_in_game"] == 0 and report["final"] == 0
    diff = r["function_diff"]; assert diff["unexplained_changes"] == 0 and len(diff["changed_exports"]) == 5
    return r, sorted(names)


def main():
    directory = ROOT / (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR)
    env = Env(directory)
    result = {"label": "OFFLINE emitted-bytecode replay (reread package JSON) - not Unreal execution, not in-game evidence",
              "model": {"path": "tools/r8b_023/fade_model_023.py", "sha256": MODEL_SHA}}
    result["threshold_cases"] = thresholds(env)
    result["rtl_invariants"] = rtl_invariants(env)
    result["corpus_60fps"] = corpus(env)
    result["lifecycle_cases"] = lifecycle_cases(env)
    result["lifecycle_3000"] = lifecycle(env)
    result["frame_audit"] = frame_audit(env, directory)
    result["native_signatures"] = native_cross_check(directory)
    r, names = validator(directory)
    result["validator"] = {"status": r["status"], "fade_fixtures": names, "return_contract_fixtures": len(r["return_contract_fixtures"]), "RichTextStyleGate_bindings": 14}
    result["verdict"] = "BYTECODE_REPLAY_PASS"
    if directory == ROOT / DEFAULT_DIR:
        (directory / "fade_replay.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    c, l = result["corpus_60fps"], result["lifecycle_3000"]
    print(f"PASS: emitted fade bytecode tint B frame-identical to the round-023 model: {c['lines']} corpus lines ({c['frames']} frames, boundaries == round 019, "
          f"completion {c['completion_minus_native_frames']}), {l['lines']} lifecycle seeds ({l['frames']} frames, 0 violations); {len(result['lifecycle_cases'])} lifecycle cases; "
          f"{result['threshold_cases']} threshold cases; {len(names)} fade fixtures; frame audit {result['frame_audit']['call_sites']} sites valid; offline only")


if __name__ == "__main__":
    main()
