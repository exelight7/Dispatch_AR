"""Execute the emitted reveal-control helpers. Clock inputs are injected: no engine adapter is bound/proven."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
from test_stage2 import VM, ROOT, float32


def main():
    directory = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "builds/rtl_poc/reveal_control_011")
    asset = json.loads((directory / "WBP_SubtitleBlock_AR_REVEAL_PARTIAL.json").read_text())
    inventory = json.loads((directory / "instruction_inventory.json").read_text())
    vm = VM(asset, inventory)
    spec = importlib.util.spec_from_file_location("canonical", ROOT / "tools/ue427_stock_reveal_test/segment_units.py")
    reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference); reference.MAX_UNITS = 37
    cases = []
    # Execute the actual generated immediate/animated branch predicate rather than mirroring its intended policy.
    main_code = asset["Exports"][10]["ScriptBytecode"]
    finish_id = vm.functions["Arabic Finish"]
    immediate = next(main_code[i-1]["BooleanExpression"] for i,n in enumerate(main_code) if i and n.get("StackNode")==finish_id and main_code[i-1]["$type"].endswith("EX_JumpIfNot, UAssetAPI"))
    def immediate_condition(node, animate):
        if node["$type"].endswith("EX_LocalVariable, UAssetAPI"):
            assert node["Variable"]["New"]["Path"]==["CallFunc_GetOptionValue_ReturnValue_2"]
            return animate
        assert node["$type"].endswith("EX_CallMath, UAssetAPI")
        return vm.native(node["StackNode"],[immediate_condition(x,animate) for x in node["Parameters"]])

    def begin(content, speaker="", animate=True):
        vm.run("Arabic Cancel")
        markup = vm.run("Build Arabic Markup", (content, speaker))
        timing_markup = vm.run("Build Arabic Timing", (content, speaker))
        markup = markup.encode("utf-16-le", errors="surrogatepass").decode("utf-16-le")
        timing_markup = timing_markup.encode("utf-16-le", errors="surrogatepass").decode("utf-16-le")
        expected = reference.build_markup(content, speaker)
        assert markup == timing_markup and (markup, vm.state["ArabicUnitCount"], vm.state["ArabicSpeakerUnits"]) == expected[:3]
        delays = vm.state["ArabicUnitDelays"]
        assert len(delays) == expected[1], (content, delays, expected)
        assert all(abs(x-y) <= max(1e-6, 1e-6*abs(y)) for x,y in zip(delays,expected[3])), (delays,expected[3])
        vm.state["bArabicActive"] = True
        vm.state["bArabicProtoSuppressed"] = True
        vm.run("Set Threshold Arabic", (vm.state["ArabicSpeakerUnits"] - 1,))
        vm.run("Arabic Begin Reveal")
        if immediate_condition(immediate,animate): vm.run("Arabic Finish", (True,))
        if animate and expected[1]>expected[2] and sum(expected[3])>0:
            assert not vm.state["ArabicFinished"] and vm.state["ArabicSchedulerArmed"]
        return expected

    def broadcasts(): return sum(name == "Broadcast" for name, _ in vm.effects)
    def advance(delta, generation=None):
        epoch = vm.state["ArabicGeneration"] if generation is None else generation
        vm.run("Arabic Advance Budget", (float32(delta), epoch))
    def done():
        assert vm.state["ArabicFinished"] and not vm.state["bArabicActive"] and not vm.state["ArabicSchedulerArmed"]
        assert vm.state["ArabicThreshold"] == vm.state["ArabicUnitCount"] - 1
        assert vm.state["ArabicCurrentUnit"] <= 36
    def check_pairing(start):
        colors = [a[0] for name, a in vm.effects[start:] if name == "SetContentColorAndOpacity"]
        assert len(colors) % 2 == 0 and all(colors[i] == colors[i+1] for i in range(0,len(colors),2))
        assert not any(name in ("SetText", "SetTextStyleSet") for name,_ in vm.effects[start:])

    for label, content, speaker in [("1 unit", "سلام", ""), ("speaker only", "", "المحقق"), ("speaker + 1", "سلام", "المحقق"),
                                    ("37 units", " ".join(["كلمة"]*37), ""), ("overflow 80 -> 37", " ".join(["كلمة"]*80), ""),
                                    ("combining/emoji", "السَّلَامُ 😀 أ\u0301", ""), ("zero-delay unit", "\u0301", "")]:
        before = broadcasts(); expected = begin(content,speaker); start=len(vm.effects)
        advance(sum(expected[3])+1); done(); assert broadcasts()==before+1
        vm.run("Arabic Finish", (False,)); assert broadcasts()==before+1
        check_pairing(start); cases.append(label)
    for label,half in [("skip at start",False),("skip halfway",True)]:
        before=broadcasts();expected=begin(" ".join(["كلمة"]*10));start=len(vm.effects)
        if half:advance(sum(expected[3])/2)
        vm.run("Arabic Skip");done();assert broadcasts()==before+1;check_pairing(start);cases.append(label)
    before=broadcasts();begin(" ".join(["كلمة"]*10));advance(.11);epoch=vm.state["ArabicGeneration"];vm.run("Arabic Cancel")
    assert not vm.state["ArabicSchedulerArmed"] and not vm.state["bArabicActive"] and not vm.state["ArabicFinished"]
    assert vm.state["ArabicCurrentUnit"]==vm.state["ArabicThreshold"]==-1
    assert vm.state["ArabicUnitCount"]==vm.state["ArabicSpeakerUnits"]==0 and vm.state["ArabicUnitDelays"]==[]
    advance(100,epoch);assert broadcasts()==before;cases.append("Stop while revealing")
    before=broadcasts();begin("سلام");advance(1);done();vm.run("Arabic Cancel");assert broadcasts()==before+1;cases.append("Stop after finish")
    before=broadcasts()
    for text in ["أ أ أ", "ب ب", "ج"]:
        begin(text);advance(1);done();vm.run("Arabic Cancel")
    assert broadcasts()==before+3;cases.append("pool A -> B -> C")
    before=broadcasts();begin("سلام بالعالم",animate=False);done();assert broadcasts()==before+1;cases.append("animation disabled")
    # This is a conditional clock-port contract, NOT evidence of Proto's actual paused accumulator source.
    for flag in [False,True]:
        begin("سلام");vm.state["Animate While Paused"]=flag;epoch=vm.state["ArabicGeneration"]
        vm.run("Arabic Advance Clocks", (0.0,float32(.11),epoch))
        assert vm.state["ArabicFinished"] is flag
        if not flag:vm.run("Arabic Advance Clocks",(float32(.11),float32(.11),epoch));done()
    cases.append("pause/unpause injected clock contract (native equivalence unproven)")
    # A stale callback must not advance a later pool generation.
    begin("أ أ");old=vm.state["ArabicGeneration"];vm.run("Arabic Cancel");begin("ب ب ب");advance(99,old)
    assert vm.state["ArabicCurrentUnit"]==-1;cases.append("stale generation rejected")
    # Broadcast can synchronously release/reuse the block: the returning old budget must not touch the new line.
    begin("أ");start_epoch=vm.state["ArabicGeneration"]
    def reuse():
        vm.on_finish=None
        begin("ب ب ب")
    vm.on_finish=reuse;advance(10,start_epoch)
    assert vm.state["ArabicGeneration"]!=start_epoch and vm.state["ArabicCurrentUnit"]==-1;cases.append("reentrant finish/pool reuse")
    # A late native Proto completion is ignored while the block belongs to Arabic.
    before=broadcasts();vm.run("On Text Finished Letter by Letter Print",(True,));assert broadcasts()==before;cases.append("old Proto finish suppressed")
    for outline in [False,True]:
        for large in [False,True]:
            vm.state["Has Outline"]=outline
            vm.native_properties[("SubtitleProtoText","ProtoTextStyleSet")]=-30 if large else -29
            vm.calls_with_targets.clear();vm.run("Arabic Apply Style")
            calls=[x for x in vm.calls_with_targets if x[0]=="SetTextStyleSet"]
            selected=("DT_AR_Outline" if outline else "DT_AR_Fill")+("_Large" if large else "")
            shadow="DT_AR_Fill"+("_Large" if large else "")
            assert [(x[1],x[2][0]) for x in calls]==[("ArabicForegroundRichText",vm.state[selected]),("ArabicShadowRichText",vm.state[shadow])]
    cases.append("all four style variants and shared fill shadow")
    vm.state["Wrap Text Length"]=840.0;vm.effects.clear();vm.run("Arabic Apply Wrap")
    assert [args for name,args in vm.effects if name=="SetTextWrapAt"]==[["ArabicForegroundRichText",840.0],["ArabicShadowRichText",840.0]]
    cases.append("stock wrap utility paired")
    proc=subprocess.run(["dotnet",str(ROOT/"tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll"),"--validate-arabic-wbp-reveal",str(ROOT),str(directory)],capture_output=True,text=True,encoding="utf-8")
    assert proc.returncode==0,proc.stderr[-2500:]
    result=json.loads(proc.stdout);assert result["errors"]==0 and len(result["negative_tests"])>=6
    report=json.loads((directory/"reveal_verification.json").read_text());assert report["status"]=="R8B_WBP_STAGE2_REVEAL_PARTIAL" and report["clock_adapter_bound"] is False and report["pause_equivalence_proven"] is False
    print(f"PASS: emitted reveal control {len(cases)} lifecycle cases +6 negative fixtures; deterministic partial artifact; native pause-clock adapter UNBOUND/NOT_PROVEN")


if __name__=="__main__":main()
