"""Replay the EMITTED 012 clock-adapter Kismet against the round-012 NativeProto model (tools/proto_binary_analysis/clock_model_012.py).

The engine stub is clock_model_012.World (UWorld::Tick time update, FTimerManager strict expiry, pending sets outside the
tick, same object+function replaces). K2_SetTimer/K2_ClearTimer/GetTimeSeconds/GetUnpausedTimeSeconds are bound to it.
This is an offline evaluator of reread package bytecode; it is not Unreal execution and not an in-game test.
python -X utf8 tools/asset_inspector/test_clock.py [builds/rtl_poc/reveal_clock_012]
"""
import importlib.util
import json
import math
import random
import subprocess
import sys
from test_stage2 import VM, ROOT, float32

NAME = "WBP_SubtitleBlock_AR_REVEAL_CLOCK"
DEFAULT_DIR, VALIDATE, REPORT = "builds/rtl_poc/reveal_clock_012", "--validate-arabic-wbp-clock", "clock_verification.json"  # test_repair_019.py rebinds
TARGET = "Arabic Clock Fired"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


model = load("tools/proto_binary_analysis/clock_model_012.py", "clock_model")
reference = load("tools/ue427_stock_reveal_test/segment_units.py", "canonical"); reference.MAX_UNITS = 37


class Engine:
    """Binds the block's reflected engine calls to one clock_model World."""
    def __init__(self, vm):
        self.vm, self.w, self.set_calls = vm, model.World(), 0
        params = lambda f: [p for p in vm.exports[vm.functions[f] - 1]["LoadedProperties"] if "CPF_Parm" in p["PropertyFlags"]]
        def set_timer(obj, fname, time, looping, delay, variance):
            assert obj == "self" and not looping and delay == variance == 0
            assert fname in vm.functions and not params(fname), "K2_SetTimer target must exist with zero parameters"
            self.set_calls += 1
            if time > 0: self.w.set_timer(("vm", fname), float(time), lambda: vm.run(fname))
            else: self.w.clear_timer(("vm", fname))   # FTimerManager: rate <= 0 clears
        self.natives = {"K2_SetTimer": set_timer, "K2_ClearTimer": lambda obj, fname: self.w.clear_timer(("vm", fname)),
                        "GetTimeSeconds": lambda obj: float(self.w.time), "GetUnpausedTimeSeconds": lambda obj: float(self.w.unpaused)}

    def armed(self): return ("vm", TARGET) in self.w.timers


class Line:
    """Observes reveal/finish frames of the emitted block (one per world)."""
    def __init__(self, vm):
        self.vm, self.reveal, self.finish, self.frame, self.last = vm, {}, [], 0, -1
        vm.on_finish = lambda: self.finish.append(self.frame)

    def observe(self):
        for i in range(self.last + 1, self.vm.state["ArabicCurrentUnit"] + 1): self.reveal[i] = self.frame
        self.last = max(self.last, self.vm.state["ArabicCurrentUnit"])

    def slate_tick(self):
        self.vm.run("Tick", (None, math.nan))   # InDeltaTime is never read: NaN would poison any use
        self.observe()


def fresh(asset, inventory):
    vm = VM(asset, inventory); vm.engine = Engine(vm); return vm


def begin_raw(vm, delays, awp):
    vm.run("Arabic Cancel")
    vm.state.update({"ArabicUnitDelays": [float32(x) for x in delays], "ArabicUnitCount": len(delays), "ArabicSpeakerUnits": 0,
                     "bArabicActive": True, "bArabicProtoSuppressed": True, "Animate While Paused": awp})
    vm.run("Set Threshold Arabic", (-1,)); vm.run("Arabic Begin Reveal")


def replay(asset, inventory, seed, awp, hidden_rate=0.0):
    """Port of clock_model_012.run with the model Arabic kept as a cross-check and the emitted VM added."""
    rng = random.Random(seed)
    n = rng.randint(1, 37)
    pend = [rng.choice([0.0, 0.025, 0.025, 0.05, 0.1, 0.3]) for _ in range(n + 1)]
    vm = fresh(asset, inventory); w = vm.engine.w; line = Line(vm)
    for _ in range(rng.randint(0, 200)): w.tick(rng.uniform(1 / 144, 1 / 20), False, 1.0)
    nat, ar = model.NativeProto(w, pend, awp), model.Arabic(w, pend[:n], awp)
    nat.start(0); ar.begin(0); begin_raw(vm, pend[:n], awp); line.observe()
    paused, dil = False, 1.0
    for frame in range(1, 3000):
        if rng.random() < 0.01: paused = not paused
        if rng.random() < 0.005: dil = rng.choice([1.0, 0.5, 0.25, 2.0])
        dt = rng.uniform(1 / 240, 1 / 20) if rng.random() > 0.01 else rng.uniform(0.1, 0.4)
        nat.frame = ar.frame = line.frame = frame
        w.tick(dt, paused, dil); line.observe()
        if rng.random() >= hidden_rate:
            ar.slate_tick(); line.slate_tick()
        if nat.finish and ar.finish and line.finish and frame > max(nat.finish[0], ar.finish[0][0], line.finish[0]) + 5: break
    return n, nat, ar, line, vm


def main():
    directory = ROOT / (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR)
    asset = json.loads((directory / (NAME + ".json")).read_text())
    inventory = json.loads((directory / "instruction_inventory.json").read_text())
    stats = {}
    for awp in (False, True):
        exact = worst = 0
        for seed in range(500):
            n, nat, ar, line, vm = replay(asset, inventory, seed, awp)
            assert len(line.finish) == 1 and line.finish[0] == line.reveal[n - 1], (seed, awp, line.finish)
            assert line.reveal == ar.reveal and line.finish == [f for f, _ in ar.finish], (seed, awp, "emitted bytecode != adapter model")
            assert not vm.engine.armed() and vm.state["ArabicClockRemainder"] == -1
            diff = [line.reveal[i] - nat.reveal[i] for i in range(n)]
            if not awp:
                assert not any(diff), (seed, diff)   # AWP=false: frame-identical to NativeProto
            else:
                assert vm.engine.set_calls == 0, "AWP=true must never start a world timer"
                assert all(-1 <= d <= 1 for d in diff), (seed, diff)
            exact += not any(diff); worst = max([worst] + [abs(d) for d in diff])
        stats[awp] = (exact, worst)
    hidden = []
    for seed in range(100):
        n, nat, ar, line, vm = replay(asset, inventory, seed, True, hidden_rate=0.3)
        assert len(line.finish) == 1 and vm.state["ArabicCurrentUnit"] == n - 1 and line.reveal == ar.reveal
        hidden += [line.reveal[i] - nat.reveal[i] for i in range(n)]
    assert min(hidden) >= -1

    # Lifecycle cases on real text lines (Build Arabic Timing ledger), with the engine stub.
    main_code = asset["Exports"][10]["ScriptBytecode"]
    vm0 = fresh(asset, inventory); finish_id = vm0.functions["Arabic Finish"]
    immediate = next(main_code[i - 1]["BooleanExpression"] for i, n in enumerate(main_code) if i and n.get("StackNode") == finish_id and main_code[i - 1]["$type"].endswith("EX_JumpIfNot, UAssetAPI"))
    def branch(vm, node, animate):
        if node["$type"].endswith("EX_LocalVariable, UAssetAPI"): return animate
        return vm.native(node["StackNode"], [branch(vm, x, animate) for x in node["Parameters"]])
    cases = []

    def text(vm, line, content, speaker="", animate=True, awp=False):
        vm.run("Arabic Cancel")
        markup = vm.run("Build Arabic Markup", (content, speaker)); vm.run("Build Arabic Timing", (content, speaker))
        expected = reference.build_markup(content, speaker)
        assert (vm.state["ArabicUnitCount"], vm.state["ArabicSpeakerUnits"]) == expected[1:3]
        vm.state.update({"bArabicActive": True, "bArabicProtoSuppressed": True, "Animate While Paused": awp})
        vm.run("Set Threshold Arabic", (vm.state["ArabicSpeakerUnits"] - 1,)); vm.run("Arabic Begin Reveal")
        if branch(vm, immediate, animate): vm.run("Arabic Finish", (True,))
        line.last = -1; line.observe(); return list(vm.state["ArabicUnitDelays"])
    def frames(vm, line, count, paused=False, dt=1 / 60):
        for _ in range(count):
            line.frame += 1; vm.engine.w.tick(dt, paused, 1.0); line.observe(); line.slate_tick()
    def native_for(vm, delays, awp=False):
        nat = model.NativeProto(vm.engine.w, delays + [0.025], awp); nat.start(0); return nat
    def done(vm):
        assert vm.state["ArabicFinished"] and not vm.state["bArabicActive"] and not vm.engine.armed() and vm.state["ArabicClockRemainder"] == -1

    def setup(): vm = fresh(asset, inventory); return vm, Line(vm)
    words = lambda k: " ".join(["كلمة"] * k)

    vm, line = setup(); nat = native_for(vm, text(vm, line, "سلام بالعالم اليوم"))
    def sync(nat, line): nat.frame = line.frame
    for _ in range(300): line.frame += 1; sync(nat, line); vm.engine.w.tick(1 / 60, False, 1.0); line.observe(); line.slate_tick()
    done(vm); assert line.finish == [line.reveal[max(line.reveal)]] and line.reveal == nat.reveal; cases.append("normal reveal == NativeProto")
    frames(vm, line, 300); assert len(line.finish) == 1; cases.append("finish once (300 extra frames)")
    vm.run("Arabic Finish", (False,)); assert len(line.finish) == 1; cases.append("finish twice -> one broadcast")

    for label, k in [("37-unit line", 37), ("overflow 80 -> 37", 80)]:
        vm, line = setup(); nat = native_for(vm, text(vm, line, words(k)))
        for _ in range(900): line.frame += 1; sync(nat, line); vm.engine.w.tick(1 / 60, False, 1.0); line.observe(); line.slate_tick()  # merged overflow tail is ~8 s
        done(vm); assert vm.state["ArabicUnitCount"] == 37 and vm.state["ArabicCurrentUnit"] == 36 and line.reveal == nat.reveal and len(line.finish) == 1
        cases.append(label + " == NativeProto")

    vm, line = setup(); nat = native_for(vm, text(vm, line, words(10)))
    pattern = [False] * 3 + [True] * 200 + [False] * 300
    for paused in pattern:
        line.frame += 1; sync(nat, line); vm.engine.w.tick(1 / 60, paused, 1.0); line.observe(); line.slate_tick()
        if paused and line.frame == 203: frozen_at = vm.state["ArabicCurrentUnit"]
    assert frozen_at == max((k for k, f in line.reveal.items() if f <= 3), default=-1)
    done(vm); assert line.reveal == nat.reveal and len(line.finish) == 1; cases.append("pause freezes / resume continues (AWP=false) == NativeProto")

    vm, line = setup(); nat = native_for(vm, text(vm, line, words(10), awp=True), awp=True)
    for _ in range(400): line.frame += 1; sync(nat, line); vm.engine.w.tick(1 / 60, True, 1.0); line.observe(); line.slate_tick()
    done(vm); assert vm.engine.set_calls == 0 and len(line.finish) == 1 and all(abs(line.reveal[i] - nat.reveal[i]) <= 1 for i in line.reveal)
    cases.append("AWP reveal while paused via Tick (no world timer, <=1 frame)")

    vm, line = setup(); delays = text(vm, line, words(10)); frames(vm, line, 18)
    assert 0 < vm.state["ArabicCurrentUnit"] < 9 and vm.engine.armed()
    vm.run("Arabic Skip"); done(vm); frames(vm, line, 200); assert line.finish == [18] and vm.state["ArabicCurrentUnit"] == 9
    cases.append("skip halfway clears timer, single finish")

    for stop in ("Stop Displaying Line", "Arabic Cancel"):
        vm, line = setup(); text(vm, line, words(10)); frames(vm, line, 10); assert vm.engine.armed()
        vm.run(stop); assert not vm.engine.armed() and vm.state["ArabicClockRemainder"] == -1 and vm.state["ArabicClockStamp"] == 0
        frames(vm, line, 300); assert not line.finish and vm.state["ArabicCurrentUnit"] == -1
    cases.append("Stop during reveal clears timer, no late finish")

    vm, line = setup(); text(vm, line, words(10)); frames(vm, line, 7); assert vm.engine.armed()
    line.reveal, line.last = {}, -1; start = line.frame; nat = native_for(vm, text(vm, line, words(6)))
    assert sum(k[0] == "vm" for k in vm.engine.w.timers) == 1, "same object+function must replace the stale timer"
    for _ in range(300): line.frame += 1; nat.frame = line.frame - start; vm.engine.w.tick(1 / 60, False, 1.0); line.observe(); line.slate_tick()
    done(vm); assert {k: f - start for k, f in line.reveal.items()} == nat.reveal and len(line.finish) == 1
    cases.append("pool A -> B replaces stale timer; B == NativeProto")

    vm, line = setup(); text(vm, line, "أ ب"); state = {}
    def reuse():   # Finish broadcast inside the timer callback synchronously reuses the block
        line.finish.append(line.frame); vm.on_finish = lambda: line.finish.append(line.frame)
        state["gen"] = vm.state["ArabicGeneration"]; state["start"] = line.frame
        state["nat"] = native_for(vm, text(vm, line, words(5))); state["nat"].frame = 0
    vm.on_finish = reuse
    for _ in range(400):
        line.frame += 1
        if "nat" in state: state["nat"].frame = line.frame - state["start"]
        vm.engine.w.tick(1 / 60, False, 1.0); line.observe(); line.slate_tick()
    assert vm.state["ArabicGeneration"] == state["gen"] + 1 and len(line.finish) == 2; done(vm)
    cases.append("reentrant finish -> pool reuse inside timer callback; stale line never re-arms")

    vm, line = setup(); text(vm, line, "سلام بالعالم", animate=False); done(vm); frames(vm, line, 100); assert line.finish == [0]
    cases.append("animation disabled: Begin arms, Finish(true) clears")

    vm, line = setup(); text(vm, line, "́"); done(vm); assert line.finish == [0]
    vm, line = setup(); text(vm, line, "سلام", "المحقق"); assert vm.state["ArabicCurrentUnit"] == vm.state["ArabicSpeakerUnits"] - 1 >= 0 and vm.engine.armed()
    frames(vm, line, 60); done(vm); cases.append("zero-delay leading units (combining-only line, speaker prefix)")

    for awp in (False, True):
        vm, line = setup(); vm.run("Arabic Cancel"); vm.state["Animate While Paused"] = awp; vm.effects.clear()
        before = json.dumps(vm.state, sort_keys=True, default=str); timers = dict(vm.engine.w.timers)
        vm.run("Tick", (None, math.nan))
        assert json.dumps(vm.state, sort_keys=True, default=str) == before and not vm.effects and vm.engine.w.timers == timers and vm.engine.set_calls == 0
    cases.append("English/inactive Tick is a no-op")

    proc = subprocess.run(["dotnet", str(ROOT / "tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll"), VALIDATE, str(ROOT), str(directory)],
                          capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr[-2500:]
    result = json.loads(proc.stdout); names = {x["fixture"] for x in result["negative_tests"]}
    required = {"Finish without ClearTimer", "Cancel without ClearTimer", "wrong timer function-name string", "Clock Fired with parameters",
                "Paused Clock without AWP guard", "Arm Clock starting timer in AWP mode", "missing FMax", "Blueprint Tick disabled"}
    assert result["errors"] == 0 and required <= names and len(names) >= 14
    report = json.loads((directory / REPORT).read_text())
    assert report["deterministic"] and report["roundtrip"] and report["unexpected_changes"] == 0 and report["tested_in_game"] == 0 and report["final"] == 0
    print(f"PASS: emitted clock adapter replay AWP=false {stats[False][0]}/500 frame-identical to NativeProto; AWP=true {stats[True][0]}/500 identical, "
          f"max {stats[True][1]} frame; {len(cases)} lifecycle cases; {len(names)} negative fixtures; offline only")


if __name__ == "__main__":
    main()
