"""Assemble the non-locres text, image and video coverage reports from saved evidence.

python -X utf8 tools/coverage/build_coverage_reports.py
Inputs (all inside the workspace): reports/coverage/cooked_text_scan.json, reports/coverage/evidence/*.json,
reports/all_asset_paths.json, extracted/**/*.ini, translation/source/*.json.
Outputs: reports/coverage/{non_locres_text,image_localization,video_localization}.json (+ .md written by hand).
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
COV = ROOT / "reports/coverage"
PLACEHOLDER = re.compile(r"(?i)sample|^text block$|button text|title text|subtitle text|placeholder|^x+[/%°a-z]*$|xx|"
                         r"^\[.*\]$|long text|long (power|setting)|setting name|hero (name|subtitle|keyword|title)|"
                         r"power name|upgrade name|scenario (name|title)|caller name|episode name|missing data|err_|error_|"
                         r"^[\W\d_]*$|^[a-z]{1,3}$|sasasa|onionion|this is where|^pivot$|framenum|story_episodetext|"
                         r"characters allowed|character limit|^dispatch x\.x\.x$|^\s*\|\s*shift x$|^roboto$|^font$|^\d+[%s]?$")
DEV = re.compile(r"DebugTools|Sandbox|Playtest|DevMenu|HackingMenu|CheatManager|AVSyncTest|DEBUG ONLY|Dev Cheat")


def sources():
    rows = []
    for path in sorted((ROOT / "translation/source").glob("*.json")):
        rows += json.loads(path.read_text(encoding="utf-8"))
    return rows


def non_locres():
    rows = sources()
    ids = {(r["namespace"], r["key"]) for r in rows}
    by_key = {r["key"] for r in rows}
    scan = json.loads((COV / "cooked_text_scan.json").read_text(encoding="utf-8"))
    paths = [e["path"] for e in json.loads((ROOT / "reports/all_asset_paths.json").read_text(encoding="utf-8"))]
    items = []

    def add(source, kind, count, cls, evidence, action, examples=None):
        items.append({"source": source, "kind": kind, "records": count, "class": cls, "evidence": evidence,
                      "action": action, "examples": (examples or [])[:8]})

    tables = sorted(p for p in paths if re.search(r"/ST_[^/]*\.uasset$", p))
    add("String tables (ST_*)", "StringTable", len(tables), "LOCALIZED_ALREADY",
        "Entries are gathered into locres under the table namespace; ST_DispatchSettings, ST_TutorialText, ST_Hacky104/105Names and "
        "ST_HackyHeroNames were exported with UAssetAPI and every entry matched a translated identity; the other tables are referenced "
        "by manifest contexts of translated records.", "None", [t.rsplit("/", 1)[1] for t in tables])
    loc = scan["localizable_texts"]
    ok = [r for r in loc if r["status"] == "LOCALIZED_ALREADY"]
    dev = [r for r in loc if r["status"] != "LOCALIZED_ALREADY"]
    add("Localizable FText serialized in cooked WBP/DA/DT/BP packages", "FText (Base history)", len(ok), "LOCALIZED_ALREADY",
        f"{len(ok)}/{len(loc)} distinct namespace/key/source triples found in 1,642 cooked UI/data packages have a translated identity.",
        "None")
    add("Localizable FText without a locres identity", "FText (Base history)", len(dev), "EDITOR_ONLY",
        "All owners are DebugTools/ or Sandbox/ widgets (debug menus, playtest configurators, QTE prototypes); none is in any shipped culture's locres.",
        "No translation", [f"{r['en'][:40]} ({r['files'][0].rsplit('/', 1)[1]})" for r in dev])
    inv = scan["culture_invariant_texts"]
    buckets = {"EDITOR_ONLY": [], "TECHNICAL_NOT_USER_VISIBLE": [], "UNKNOWN": []}
    for r in inv:
        if all(DEV.search(f) for f in r["files"]) or DEV.search(r["en"]):
            buckets["EDITOR_ONLY"].append(r)
        elif PLACEHOLDER.search(r["en"].strip()) or len(r["en"].strip()) <= 1:
            buckets["TECHNICAL_NOT_USER_VISIBLE"].append(r)
        else:
            buckets["UNKNOWN"].append(r)
    notes = {"EDITOR_ONLY": "Culture-invariant FText owned by debug/sandbox widgets.",
             "TECHNICAL_NOT_USER_VISIBLE": "Culture-invariant designer preview/placeholder text (replaced at runtime) or symbols/numbers.",
             "UNKNOWN": "Culture-invariant FText (ETextFlag::CultureInvariant) in shipping widgets: it can never be localized through locres. "
                        "Whether it is overwritten at runtime or visible is not statically known; the same English shows in all 16 shipped cultures."}
    for cls, rows_ in buckets.items():
        add("Culture-invariant FText in cooked widgets", "FText (CultureInvariant)", len(rows_), cls, notes[cls],
            "In-game observation; a visible case needs a WBP edit (REQUIRES_UNSUPPORTED_EDIT with current tooling)" if cls == "UNKNOWN" else "None",
            [f"{r['en'][:40]} ({r['files'][0].rsplit('/', 1)[1]})" for r in rows_])
    cfg = (ROOT / "extracted/Dispatch/Config/DefaultGame.ini").read_text(encoding="utf-8")
    ns = re.findall(r'NSLOCTEXT\("([^"]*)", "([^"]*)", "([^"]*)"\)', cfg)
    have = [x for x in ns if x[1] in by_key]
    names = [x for x in ns if x[1] not in by_key]
    add("DefaultGame.ini [DispatchCommentarySettings] NSLOCTEXT speaker names/titles", "Config FText", len(have), "LOCALIZED_ALREADY",
        "Package namespace [/Script/Dispatch] is stripped in locres (e.g. key 5524BBF0... 'Coupé' is translated in 101).", "None",
        [x[2] for x in have])
    add("DefaultGame.ini commentary speaker real-person names", "Config FText", len(names), "RETAINED_PROPER_NAME",
        "No locres identity in any of the 17 shipped cultures; these are names of the real cast/crew (and the group THOT SQUAD). "
        "Kept in their original Latin spelling by project policy (STYLE_GUIDE).", "None (policy)", [x[2] for x in names])
    loctable = re.findall(r'LOCTABLE\("([^"]+)", "([^"]+)"\)', cfg + (ROOT / "extracted/Dispatch/Config/DefaultInput.ini").read_text(encoding="utf-8"))
    add("Config LOCTABLE references", "StringTable reference", len(loctable), "LOCALIZED_ALREADY",
        "References ST_CommentarySpeakerTitles and ST_InputBindingPresets, whose entries are translated.", "None")
    add("Engine BaseEngine.ini [Core.System] serialization error texts", "Config FText", 2, "LOCALIZED_ALREADY",
        "Added to translation/engine_scope.json this round (RUNTIME_CONFIRMED).", "None")
    add("Engine/Niagara ini LOD-group, buffer-visualization and quality-level names", "Config FText", 20, "EDITOR_ONLY",
        "Editor/developer setting lists (see reports/coverage/engine_classification.json).", "None")
    prof = [p for p in paths if "/DT_Profanities" in p and p.endswith(".uasset")]
    add("Profanity filter DataTables", "DataTable", len(prof), "TECHNICAL_NOT_USER_VISIBLE",
        "Word lists for the subtitle profanity filter, one per shipped language; there is no Arabic list, so Arabic subtitles cannot be "
        "filtered by this mechanism (behaviour for an unknown culture is NOT_PROVEN).", "Optional future: an Arabic word list requires a new DataTable (cook) and Blueprint routing",
        [p.rsplit("/", 1)[1] for p in prof])
    styles = [p for p in paths if re.search(r"/DT_.*(RichText|TextStyle|Subtitles)", p) and p.endswith(".uasset")]
    add("Rich-text style DataTables", "DataTable", len(styles), "TECHNICAL_NOT_USER_VISIBLE",
        "Font/style rows, no display text; relevant to font and RTL work, not to translation.", "See reports/fonts/", [p.rsplit("/", 1)[1] for p in styles])
    plugins = [p for p in paths if p.endswith(".uplugin")]
    add("Plugin descriptors (.uplugin)", "JSON descriptor", len(plugins), "EDITOR_ONLY",
        "FriendlyName/Description are shown only in the editor plugin browser.", "None")
    playstats = [p for p in paths if p.endswith(".playstats")]
    add("Story .playstats files", "Binary data", len(playstats), "TECHNICAL_NOT_USER_VISIBLE",
        "Choice-statistics data; the displayed sentences are ChoiceStat locres records (translated).", "None")
    icu = [p for p in paths if "Internationalization/icudt64l" in p]
    add("ICU data (icudt64l)", "ICU resource", len(icu), "TECHNICAL_NOT_USER_VISIBLE",
        "Locale data incl. ar*.res (culture names, plural rules, number formats) and line-break rules; language-neutral engine data.", "None")
    add("Online plugin messages", "locres", 46, "LOCALIZED_ALREADY", "OnlineSubsystem/Steam/Utils locres translated.", "None")
    add("Steam overlay / platform service UI", "External", 0, "TECHNICAL_NOT_USER_VISIBLE",
        "Rendered by Steam, not by game resources; out of the mod's reach.", "None")
    add("Credits", "Video", 15, "UNKNOWN", "Credits are webm movies (see VIDEO_LOCALIZATION).", "See video report")
    add("Licenses / Terms of Service body text", "Runtime-supplied text", 2, "UNKNOWN",
        "WBP_UI_Settings_Permissions+Licenses holds culture-invariant placeholders '[Licenses Text]' and '[Terms of Service Text]'; the real "
        "text is supplied at runtime by code or a platform API not visible in locres.", "In-game observation")
    report = {"items": items,
              "summary": dict(Counter(i["class"] for i in items)),
              "counts_by_class": {c: sum(i["records"] for i in items if i["class"] == c) for c in {i["class"] for i in items}},
              "note": "RETAINED_PROPER_NAME extends the five requested classes for real-person names; it is not a translation gap."}
    (COV / "non_locres_text.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return report


IMG_RULES = [  # (regex on asset path, class, context, difficulty, priority)
    (r"ButtonPrompts|_Key_|KeyboardMouse|Gamepad|XboxSeries|PS5|PS4|Switch", "LANGUAGE_NEUTRAL", "Input glyph / key legend", "-", "-"),
    (r"Logo|AdhocLogo|_SDF", "LANGUAGE_NEUTRAL", "Brand logo / icon", "-", "-"),
    (r"BannerAds|MerchPanel", "LANGUAGE_NEUTRAL", "Main-menu product art (box/album art); overlay text is localized ST_AdStrings", "-", "-"),
    (r"ChaoticCensor.*(Restricted|SDN)", "NEEDS_ARABIC", "Chaotic censorship overlay ('RESTRICTED / Please contact your supervisor')", "LOW", "MEDIUM"),
    (r"ScenarioCrimeArt|Extras_Analytics|Map/Locations", "LANGUAGE_NEUTRAL", "Illustration; any lettering is diegetic (e.g. RESCUE on a helicopter), visually checked samples", "-", "-"),
    (r"Dossier_Still", "NEEDS_ARABIC", "Hero database dossier still with '[UNAVAILABLE]' stamp", "MEDIUM", "LOW"),
    (r"TutorialTempImages", "NEEDS_ARABIC", "Tutorial screenshot with English UI (name says Temp; usage unverified)", "HIGH", "LOW"),
    (r"/Extras/Comic|ComicsCover|Comics_0", "NEEDS_ARABIC", "Deluxe extras comic pages/covers with English lettering", "VERY_HIGH", "LOW"),
    (r"ArtBook|Artbook", "NEEDS_ARABIC", "Deluxe extras artbook pages with English annotations", "VERY_HIGH", "LOW"),
    (r"SavePoints/Images", "LANGUAGE_NEUTRAL", "Story save-point still; any text is diegetic signage", "-", "-"),
    (r"Signature", "LANGUAGE_NEUTRAL", "Hand signature art", "-", "-"),
    (r"Sandbox|DebugTools|Temp_ScenarioArt|Placeholder|PowerTwoTest|RenderTarget", "NOT_RUNTIME", "Sandbox/debug/placeholder art", "-", "-"),
]


def images():
    probe = {r["asset"]: r for r in json.loads((COV / "evidence/texture_probe_all.json").read_text(encoding="utf-8"))}
    ocr = {r["asset"]: r for r in json.loads((COV / "evidence/texture_probe_ocr.json").read_text(encoding="utf-8"))}
    ocr.update({r["asset"]: r for r in json.loads((COV / "evidence/texture_probe_extras_sample_ocr.json").read_text(encoding="utf-8"))})
    out = []
    for asset, r in sorted(probe.items()):
        o = ocr.get(asset, {})
        text = [x["text"] for x in o.get("ocr", []) if x["score"] >= 0.8 and re.search("[A-Za-z]{3,}", x["text"])]
        cls, ctx, diff, prio = None, "", "-", "-"
        if not r.get("decoded"):
            cls, ctx = "UNREADABLE", r.get("reason", "")
        else:
            for pattern, c, context, d, p in IMG_RULES:
                if re.search(pattern, asset):
                    cls, ctx, diff, prio = c, context, d, p
                    break
            if cls is None:
                cls = "NO_TEXT" if not text else "ENGLISH_TEXT_RUNTIME"
                ctx = "OCR found no Latin words (not every image was inspected by eye)" if not text else "OCR text; review needed"
        out.append({"asset": asset, "format": r.get("format"), "width": r.get("width"), "height": r.get("height"),
                    "class": cls, "context": ctx, "replacement_difficulty": diff, "priority": prio,
                    "ocr_text": text[:8], "ocr_run": asset in ocr})
    report = {"textures_probed": len(out), "summary": dict(Counter(i["class"] for i in out)),
              "method": "All 995 Dispatch/** T_* textures decoded from temporary extracted copies (texture2ddecoder); OCR (RapidOCR) on 835 "
                        "non-extras textures and a 16-image sample of extras pages; classification rules by path + OCR + spot visual checks.",
              "replacement_assets_present": 0, "images": out}
    (COV / "image_localization.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return report


VIDEO_RULES = [  # (path pattern, class, context, priority)
    (r"/(AVSyncTest|TestClips|AudioGapTest)/", "NOT_RUNTIME", "engineering A/V test clip", "-"),
    (r"Credits", "BURNED_IN_TEXT", "end credits: English role titles + names burned into the video", "LOW"),
    (r"/StartupMovies/", "LANGUAGE_NEUTRAL", "studio logo sting", "-"),
    (r"/Menus/MainMenu", "LANGUAGE_NEUTRAL", "menu backdrop; OCR hits are diegetic signage only", "-"),
]


def videos():
    paths = [r["path"] for r in json.loads((ROOT / "reports/all_asset_paths.json").read_text(encoding="utf-8"))
             if re.search(r"\.(webm|mp4)$", r["path"], re.I)]
    probe = {r["movie"]: r for r in json.loads((COV / "evidence/video_probe_sample.json").read_text(encoding="utf-8"))}
    out = []
    for path in sorted(paths):
        p = probe.get(path)
        cls, ctx, prio = None, "", "-"
        for pattern, c, context, pr in VIDEO_RULES:
            if re.search(pattern, path):
                cls, ctx, prio = c, context, pr
                break
        if cls is None:
            if p:
                cls = "NO_BURNED_TEXT" if not p["ocr_frames_with_text"] else "REVIEW"
                ctx = "sampled: no subtitle stream, OCR found no text"
            else:
                cls, ctx = "NO_BURNED_TEXT_INFERRED", "not sampled; same pipeline/folder as sampled cutscenes"
        out.append({"movie": path, "class": cls, "context": ctx, "priority": prio, "sampled": bool(p),
                    "subtitle_streams": p["subtitle_streams"] if p else None,
                    "ocr_frames_with_text": p["ocr_frames_with_text"] if p else None})
    report = {"movies": len(out), "sampled": len(probe), "summary": dict(Counter(v["class"] for v in out)),
              "subtitle_route": "Dialogue subtitles are UMG text fed by localized FText (episode Line records in locres); "
                                "no sampled movie carries a subtitle stream, so Arabic subtitles come from the ar locres.",
              "method": "Inventory from reports/all_asset_paths.json; 32 movies (all 15 credits + menus/startup + cutscenes "
                        "from every episode) copied to a temp folder, streams listed and one frame per 6 s OCR'd (RapidOCR).",
              "replacement_assets_present": 0, "videos": out}
    (COV / "video_localization.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return report


def main():
    a = non_locres()
    b = images()
    c = videos()
    print(json.dumps({"non_locres": a["counts_by_class"], "images": b["summary"], "videos": c["summary"]}, indent=2))


if __name__ == "__main__":
    main()
