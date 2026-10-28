"""Round 019: the void Build Arabic Timing keeps its side effects on the round-010 96-fixture corpus (unit count, speaker
units, delay ledger vs the canonical segmenter; Build Arabic Markup unchanged), then the round-012 clock replay (500+500 seeds
vs NativeProto, lifecycle cases) runs on the repaired WBP, followed by --validate-arabic-wbp-repair-019.
Offline evaluator of reread package bytecode only; not Unreal, not in game.
python -X utf8 tools/asset_inspector/test_repair_019.py [builds/rtl_poc/r8b_repair_019]
"""
import json
import random
import sys
import test_clock
from test_stage2 import ROOT

test_clock.NAME = "WBP_SubtitleBlock_AR_R8B_REPAIR_019"
test_clock.DEFAULT_DIR, test_clock.VALIDATE, test_clock.REPORT = "builds/rtl_poc/r8b_repair_019", "--validate-arabic-wbp-repair-019", "repair_verification.json"


def ledger_check(directory):
    asset = json.loads((directory / (test_clock.NAME + ".json")).read_text())
    vm = test_clock.fresh(asset, json.loads((directory / "instruction_inventory.json").read_text()))
    canonical = test_clock.reference
    fixtures = [("مرحبا (TEST-42) بالعالم", "المحقق"), ("السعر 50 USD اليوم", ""), ("أ\n50 ب", ""),
                ('a<b & "c"', ""), (" ".join(["كلمة"] * 200), "المحقق"), ("السَّلَامُ", ""), ("", ""),
                (" ", ""), ("  أ", "المحقق"), ("أ\r50 ب", ""), ("أ ب ج د", ""),
                ("أ‍ب أ‌ب أ​ب", ""), ("", " ".join(["اسم"] * 40)), ("   ", "المحقق"), ("مرحبا 😀 50 اليوم", "اسم"), ("don't <b> & \"c\"", "")]
    rng = random.Random(10)   # same generator as test_stage2.py
    words = ["مرحبا", "كَلمة", "50", "!", "TEST-42", "a<b", "&", '"c"', "أ ب", "أ‍ب", "سـلام"]
    gaps = [" ", "\t", "\n", "\r", "  ", "\n "]
    for _ in range(80):
        fixtures.append(("".join(rng.choice(words) + rng.choice(gaps) for _ in range(rng.randrange(1, 75))), rng.choice(["", "المحقق", "اسم طويل"])))
    for content, speaker in fixtures:
        expected = canonical.build_markup(content, speaker)
        vm.run("Arabic Cancel")
        assert vm.run("Build Arabic Timing", (content, speaker)) is None, "Build Arabic Timing must be void"
        delays = vm.state["ArabicUnitDelays"]
        assert (vm.state["ArabicUnitCount"], vm.state["ArabicSpeakerUnits"]) == expected[1:3], (repr(content), speaker)
        assert len(delays) == expected[1] and all(abs(x - y) <= max(1e-6, 1e-6 * abs(y)) for x, y in zip(delays, expected[3])), (repr(content), delays, expected[3])
        markup = vm.run("Build Arabic Markup", (content, speaker)).encode("utf-16-le", errors="surrogatepass").decode("utf-16-le")
        assert markup == expected[0] and (vm.state["ArabicUnitCount"], vm.state["ArabicSpeakerUnits"]) == expected[1:3]
    return len(fixtures)


if __name__ == "__main__":
    n = ledger_check(ROOT / (sys.argv[1] if len(sys.argv) > 1 else test_clock.DEFAULT_DIR))
    print(f"void Build Arabic Timing ledger == canonical on {n} fixtures")
    test_clock.main()
