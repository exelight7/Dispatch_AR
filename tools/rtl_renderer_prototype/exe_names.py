"""Round 004: static reflected-name evidence for the stock-renderer and native-loading questions.

Reads the shipped EXE bytes only (hash-locked) and lists install-folder file names. Never runs anything.
python -X utf8 tools/rtl_renderer_prototype/exe_names.py
"""
import hashlib
import json
from pathlib import Path

import renderer as M

GAME = Path(json.loads((M.ROOT / "reports/investigation.json").read_text(encoding="utf-8"))["game_root"])
EXE = GAME / "Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe"
EXE_SHA256 = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923"
OUT = M.ROOT / "reports/rtl_research/renderer_repair/exe_names.json"

# UE4.27 class registration keeps the prefixed C++ name as a wide string; reflected
# function/property names are narrow UTF-8 strings. Each name must appear NUL-delimited.
WIDE, NARROW = "wide", "narrow"
GROUPS = {
    "stock_umg_classes": (WIDE, ["URichTextBlock", "URichTextBlockDecorator", "URichTextBlockImageDecorator",
                                 "UTextBlock", "URetainerBox", "UInvalidationBox", "UOverlay", "UCanvasPanel",
                                 "UWidgetSwitcher", "UImage", "UMaterialInstanceDynamic",
                                 "UMaterialParameterCollection", "UTextureRenderTarget2D", "UKismetRenderingLibrary",
                                 "UKismetMaterialLibrary", "UKismetInternationalizationLibrary", "UKismetTextLibrary"]),
    "stock_structs": (NARROW, ["RichTextStyleRow", "TextBlockStyle", "SlateFontInfo", "FontOutlineSettings",
                               "FontMaterial", "OutlineMaterial", "ColorAndOpacity", "ShadowColorAndOpacity",
                               "ShapedTextOptions", "TextFlowDirection", "TextShapingMethod",
                               "ETextFlowDirection::RightToLeft", "ETextShapingMethod::FullShaping"]),
    "rich_text_functions": (NARROW, ["SetText", "SetTextStyleSet", "SetDefaultTextStyle", "SetDefaultFont",
                                     "SetDefaultColorAndOpacity", "SetDefaultShadowColorAndOpacity",
                                     "ClearAllDefaultStyleOverrides", "GetDecoratorByClass", "SetAutoWrapText",
                                     "SetMinDesiredWidth", "SetJustification", "SetTextTransformPolicy",
                                     "RequestRender", "SetRetainRendering", "SetEffectMaterial", "SetRenderOpacity"]),
    "absent_in_427_expected": (NARROW, ["SetDefaultMaterial", "SetFontMaterial"]),
    "language_functions": (NARROW, ["GetCurrentLanguage", "GetCurrentCulture", "GetCurrentLocale",
                                    "GetNativeCulture", "GetSuitableCulture", "SetCurrentLanguage"]),
    "game_language_setting": (WIDE, ["UDispatchLanguageSetting"]),
    "reveal_channel_functions": (NARROW, ["ClearRenderTarget2D", "CreateRenderTarget2D",
                                          "DrawMaterialToRenderTarget", "SetScalarParameterValue",
                                          "SetVectorParameterValue", "K2_SetTimer", "K2_SetTimerDelegate",
                                          "ParseIntoArray", "Delay"]),
    "game_plugin_text_classes": (WIDE, ["UProtoRichTextBlock", "UProtoRichTextCharColorDecorator",
                                        "UProtoRichTextImageDecorator", "UProtoRichTextWidgetDecorator",
                                        "UCommonRichTextBlock", "UCommonTextBlock", "UCommonTextStyle"]),
    "plugin_discovery_strings": (WIDE, ["Mods/", "PLUGIN=", "EnablePlugins=", ".upluginmanifest",
                                        "AdditionalPluginDirectories", "_P.pak",
                                        "Plugin '{0}' failed to load because module '{1}' could not be found.  "
                                        "Please ensure the plugin is properly installed, otherwise consider "
                                        "disabling the plugin for this project."]),
    "script_runtimes_expected_absent": (WIDE, ["UE4SS", "UnLua", "PythonScriptPlugin"]),
}


def find(blob, name, enc):
    if enc == WIDE:
        needle, pad = name.encode("utf-16le"), b"\x00\x00"
    else:
        needle, pad = name.encode("utf-8"), b"\x00"
    hits, i = [], blob.find(pad + needle + pad)
    while i != -1 and len(hits) < 8:
        hits.append(hex(i + len(pad)))
        i = blob.find(pad + needle + pad, i + 1)
    return hits


def main():
    blob = EXE.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == EXE_SHA256, "unknown executable; evidence offsets would not apply"
    groups = {g: {n: find(blob, n, enc) for n in names} for g, (enc, names) in GROUPS.items()}
    install = sorted(str(p.relative_to(GAME)) for p in GAME.rglob("*")
                     if p.suffix.lower() in {".dll", ".modules", ".sig", ".uplugin", ".uproject", ".exe"})
    out = dict(
        evidence_class="CONFIRMED_FROM_BINARY (name presence only; not behavior)",
        exe=str(EXE.relative_to(GAME)), exe_sha256=digest,
        monolithic_rtti_FStaticallyLinkedModuleRegistrant=blob.count(b"FStaticallyLinkedModuleRegistrant"),
        groups=groups,
        missing={g: [n for n, h in v.items() if not h] for g, v in groups.items()},
        install_binaries_and_descriptors=install,
    )
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out["missing"], indent=1))
    print("monolithic RTTI hits:", out["monolithic_rtti_FStaticallyLinkedModuleRegistrant"])
    print("install files:", install)
    # Required names must exist; names expected absent must stay absent.
    for g, v in out["missing"].items():
        if "absent" in g:
            assert len(v) == len(groups[g]), f"{g}: unexpectedly present"
        else:
            assert not v, f"{g}: missing {v}"


if __name__ == "__main__":
    main()
