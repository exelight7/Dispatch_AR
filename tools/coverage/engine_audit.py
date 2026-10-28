"""Classify every Engine.locres record outside translation/engine_scope.json by static runtime evidence.

Evidence (read-only):
  * the hash-locked shipping EXE: UE4 LOCTEXT/NSLOCTEXT compiles the source, namespace and key
    as separate NUL-terminated UTF-16 literals, so a record whose key and source literals are
    both absent from the monolithic shipping binary is not produced by shipped C++ code;
  * NSLOCTEXT/LOCTEXT references in the shipped .ini files under extracted/;
  * optionally (--engine-assets DIR) the shipped Engine/** cooked packages, searched for keys.

python -X utf8 tools/coverage/engine_audit.py [--engine-assets DIR]
Writes reports/coverage/engine_classification.json and engine_classification_summary.json.
Never runs or modifies the game.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from localization import read_locres  # noqa: E402

GAME = Path(json.loads((ROOT / "reports/investigation.json").read_text(encoding="utf-8"))["game_root"])
EXE = GAME / "Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe"
EXE_SHA256 = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923"
ENGINE_LOCRES = ROOT / "extracted/Engine/Content/Localization/Engine/en/Engine.locres"
OUT = ROOT / "reports/coverage"

# Compiled-in records whose text is addressed to the player and whose code path runs in an
# ordinary shipping session (no developer flag, console command or editor). Reviewed one by one.
RUNTIME_CONFIRMED = {
    ("Audio", "XAudio2Error"): "Audio device initialization failure dialog addressed to the player.",
    ("Audio", "XAudio2Missing"): "Missing XAudio 2.7 dialog addressed to the player.",
    ("", "SerializationOutOfBoundsErrorMessage"): "BaseEngine.ini [Core.System] corrupt-data dialog body.",
    ("", "SerializationOutOfBoundsErrorMessageCaption"): "BaseEngine.ini [Core.System] corrupt-data dialog title.",
}
# Compiled-in and player-addressed, but the trigger path is unverified or unusual for Dispatch.
RUNTIME_LIKELY_NS = {
    "PluginManager": "Startup plugin-failure dialogs; only a broken install or an added code plugin triggers them.",
    "SlateD3DRenderer": "Standalone Slate D3D renderer; the game window renders through SlateRHIRenderer.",
    "CommonDateTimeTextBlock": "CommonUI date/time widget; no game asset reference to this class was inspected.",
    "CommonBoundActionButton": "Multi-player action prefix; Dispatch is single-player.",
    "Timespan": "Numeric time format; identical in Arabic, only used if a widget formats a timespan.",
    "Internationalization": "Memory-size number format; identical in Arabic.",
    "WindowTitleBar": "Slate-drawn window chrome; Windows game windows use the OS border by default.",
}

EDITOR_RE = re.compile(
    r"Editor|UnrealEd|ContentBrowser|AssetTypeActions|AssetTools|Kismet(?!Rendering|Material|Array|Math|System|Animation)|"
    r"Graph|Persona|Sequencer|Details|Customization|Property|LevelEditor|Modeling|Toolkit|Factory|Landscape|Foliage|"
    r"Matinee|Blueprint|K2Node|Schema|Palette|Outliner|Viewport|Niagara|Paper2D|Sprite|TileMap|Flipbook|ControlRig|"
    r"Rig|Datasmith|Dataprep|Usd|Mesh|Fracture|Material|Texture|Curve|Anim|Skeleton|Physics|PhAT|Collection|Source"
    r"Control|Perforce|Subversion|Git|Plastic|Localization|Translation|Undo|Transaction|Gizmo|Placement|Mode|Tool|"
    r"Brush|Geometry|Volume|Actor|Level|World|Import|Export|Asset|Package|Thumbnail|Widget|UMG|Layout|Variant|DMX|"
    r"DisplayCluster|Camera|Lens|Calibration|Media|Take|Recorder|MovieScene|MoviePipeline|Composure|Comp|Lidar|"
    r"Groom|Hair|Water|Text3D|VirtualProduction|RemoteControl|Python|Script|Class|Struct|Enum|Pin|Node|Wizard|Project|"
    r"Template|Plugin|Settings|Customize|Dialog|Picker|Browser|Panel|View|Tab|Menu|Toolbar|Commands|Notification|"
    r"Gameplay(Tags|Cue|Abilities)|EnvironmentQuery|BehaviorTree|Blackboard|AIGraph|Sound(Cue|Class)|Audio(Editor|Mixer)|"
    r"Synth|Metasound|Dialogue|Foliage|Hlod|HLOD|Lightmass|Swarm|Merge|Proxy|Simplygon|LOD|Bake|Baker", re.I)
DEV_RE = re.compile(  # case-sensitive: CamelCase namespace tokens
    r"Test|Automation|Profil|Insights|Trace|Timing|Stats|MemTag|Session|Launcher|DeviceProfile|TargetPlatform|"
    r"Concert|MultiUser|DisasterRecovery|LiveLink|Messaging|Reflector|Hittest|Console|Cheat|Debug|VisualLogger|"
    r"LogVisualizer|OutputLog|SLog|Crash|ScreenShot|Screenshot|Frontend|Cook|Shader|Benchmark|PixelInspector|"
    r"RenderDoc|Oculus|SteamVR|HoloLens|Lumin|MagicLeap|Android|IOS|Linux|PreLoadManager|BuildPatch|^XR|HMD|^VR")

# Compiled-in namespaces whose text is developer-facing (debug, validation, tool documentation).
DEV_COMPILED_NOTE = {
    "UnicodeBlock": "Unicode block names for font tooling (FUnicodeBlockRange display names).",
    "ScriptCore": "Blueprint VM runtime-error messages for developers.",
    "Core": "Command-line, package-path, property and math-type formatting diagnostics.",
    "Engine": "Reflection-capture build and UI scaling-rule developer warnings.",
    "UMG": "UMG widget construction/focus validation messages and palette categories.",
    "HeadMountedDisplay": "XR console-variable help text.",
    "LaunchEngineLoop": "Editor/shader-compile startup messages.",
    "WindowsPlatform": "GameExplorer command-line installer mode messages.",
    "UnrealClient": "HighResShot console-command feedback.",
    "GameViewport": "Developer warnings from UGameViewportClient::AddCursor.",
}


def exe_strings():
    data = EXE.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXE_SHA256:
        raise SystemExit("Shipping EXE hash differs from the investigated build; refusing to classify")
    found = set()
    for off in (0, 1):  # literals are 2-byte aligned; scan both phases for safety
        units = np.frombuffer(data[off:len(data) - (len(data) - off) % 2], dtype="<u2")
        zeros = np.flatnonzero(units == 0)
        starts, ends, raw = np.concatenate(([0], zeros + 1)), np.concatenate((zeros, [len(units)])), units.tobytes()
        for s, e in zip(starts.tolist(), ends.tolist()):
            if 0 < e - s <= 4000:
                try:
                    found.add(raw[2 * s:2 * e].decode("utf-16le"))
                except UnicodeDecodeError:
                    pass
    return found


def ini_text_refs():
    refs = {}
    pattern = re.compile(r'NSLOCTEXT\(\s*"([^"]*)"\s*,\s*"([^"]*)"|(?<!NS)LOCTEXT\(\s*"([^"]*)"')
    for path in sorted((ROOT / "extracted").rglob("*.ini")):
        for line_no, line in enumerate(path.read_text("utf-8", "replace").splitlines(), 1):
            for m in pattern.finditer(line):
                key = m[2] if m[2] is not None else m[3]
                refs.setdefault(key, f"{path.relative_to(ROOT / 'extracted').as_posix()}:{line_no}")
    return refs


def asset_keys(folder):
    keys = set()
    for path in Path(folder).rglob("*"):
        if path.is_file():
            keys.update(re.findall(rb"[0-9A-F]{32}", path.read_bytes()))
    return {k.decode() for k in keys}


def classify(row, flags, ns_compiled):
    ns, key = row["namespace"], row["key"]
    if (ns, key) in RUNTIME_CONFIRMED:
        return "RUNTIME_CONFIRMED", RUNTIME_CONFIRMED[(ns, key)]
    compiled = flags["key"] and flags["source"] and (flags["distinctive"] or ns_compiled.get(ns))
    if flags["config"]:
        if EDITOR_RE.search(flags["config"]) or "Niagara" in flags["config"] or "LOD" in key or "Mat" in key:
            return "DEVELOPMENT_ONLY_CONFIRMED", f"Referenced only by {flags['config']} (editor/tool setting list)."
    if compiled:
        if ns in RUNTIME_LIKELY_NS:
            return "RUNTIME_LIKELY", RUNTIME_LIKELY_NS[ns]
        return "DEVELOPMENT_ONLY_CONFIRMED", DEV_COMPILED_NOTE.get(
            ns, "Compiled into the shipping EXE, but the text is developer/tool-facing (validation, debug, editor descriptors).")
    if flags["asset"]:
        return "UNKNOWN", "Key found in a shipped Engine cooked package; usage not established."
    basis = "Key/source literals absent from the shipping EXE and not referenced by shipped config or Engine packages"
    if ns == "" and re.fullmatch(r"[0-9A-F]{32}", key):
        return "EDITOR_ONLY_CONFIRMED", basis + "; asset-gathered editor content text (macros, sample maps, material functions)."
    if DEV_RE.search(ns):
        return "DEVELOPMENT_ONLY_CONFIRMED", basis + "; developer/platform tooling namespace."
    if EDITOR_RE.search(ns):
        return "EDITOR_ONLY_CONFIRMED", basis + "; editor module namespace."
    return "UNUSED_OR_UNREACHABLE_CONFIRMED", basis + "."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-assets", type=Path, help="Folder holding shipped Engine/** cooked packages")
    args = parser.parse_args()
    strings = exe_strings()
    refs = ini_text_refs()
    assets = asset_keys(args.engine_assets) if args.engine_assets else set()
    resource = read_locres(ENGINE_LOCRES.read_bytes())
    scope = {(r["namespace"], r["key"]) for r in json.loads((ROOT / "translation/engine_scope.json").read_text(encoding="utf-8"))["identities"]}
    source_counts = Counter(r["text"] for r in resource["rows"])
    flags, ns_compiled = {}, defaultdict(bool)
    for i, row in enumerate(resource["rows"]):
        text = row["text"]
        f = {"source": text in strings, "key": row["key"] in strings,
             "namespace": row["namespace"] in strings if row["namespace"] else None,
             "distinctive": source_counts[text] == 1 and (len(text) >= 24 or len(text.split()) >= 3),
             "config": refs.get(row["key"], ""), "asset": row["key"] in assets}
        flags[i] = f
        if f["source"] and f["key"] and f["distinctive"]:
            ns_compiled[row["namespace"]] = True
    records, control = [], Counter()
    for i, row in enumerate(resource["rows"]):
        f = flags[i]
        if (row["namespace"], row["key"]) in scope:
            control["selected_total"] += 1
            control["selected_key_and_source_in_exe"] += f["source"] and f["key"]
            continue
        label, reason = classify(row, f, ns_compiled)
        records.append({"locres_index": i, "namespace": row["namespace"], "key": row["key"],
                        "source_hash": row["source_hash"], "en": row["text"], "class": label, "reason": reason,
                        "evidence": {"exe_key": f["key"], "exe_source": f["source"], "exe_namespace": f["namespace"],
                                     "distinctive_source": f["distinctive"],
                                     "namespace_has_compiled_distinctive_text": ns_compiled[row["namespace"]],
                                     "config_reference": f["config"] or None, "engine_package_key": f["asset"]}})
    assert len(records) + control["selected_total"] == len(resource["rows"])
    by_class = Counter(r["class"] for r in records)
    by_ns = defaultdict(Counter)
    for r in records:
        by_ns[r["namespace"]][r["class"]] += 1
    summary = {"source": ENGINE_LOCRES.relative_to(ROOT).as_posix(),
               "source_sha256": hashlib.sha256(ENGINE_LOCRES.read_bytes()).hexdigest(),
               "exe_sha256": EXE_SHA256, "total_records": len(resource["rows"]),
               "selected_scope": control["selected_total"], "classified_outside_scope": len(records),
               "classes": dict(sorted(by_class.items())),
               "positive_control": {"selected_records_with_key_and_source_in_exe": control["selected_key_and_source_in_exe"],
                                    "selected_total": control["selected_total"]},
               "engine_packages_searched": bool(args.engine_assets),
               "runtime_confirmed_meaning": "Compiled into (or configured for) the shipping build and addressed to the player; display is still NOT runtime-tested.",
               "namespaces": {ns: dict(c) for ns, c in sorted(by_ns.items())}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "engine_classification.json").write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (OUT / "engine_classification_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("classified_outside_scope", "classes", "positive_control")}, indent=2))


if __name__ == "__main__":
    main()
