"""Bounded read-only inspection of two existing JSON exports, not a new asset scan."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/rtl_research/renderer_repair"


def inspect(path):
    data = path.read_bytes()
    obj = json.loads(data.decode("utf-8-sig"))
    exports, imports = obj["Exports"], obj["Imports"]

    def resolve(ref):
        if ref == 0:
            return None
        e = (exports[ref-1] if ref > 0 else imports[-ref-1])
        return e["ObjectName"]

    tree, typed, hooks = [], [], []
    for index, export in enumerate(exports, 1):
        cls = resolve(export.get("ClassIndex", 0))
        if cls not in {"Function", "WidgetBlueprintGeneratedClass"}:
            fields = {}
            for prop in export.get("Data", []):
                n = prop.get("Name")
                if n in {"Parent", "Content", "RootWidget", "Visibility", "HorizontalAlignment",
                         "bHasScriptImplementedTick", "bHasScriptImplementedPaint"}:
                    fields[n] = prop.get("Value", prop.get("EnumValue"))
                elif n == "Slots":
                    fields[n] = [p["Value"] for p in prop.get("Value", [])]
            tree.append({"export": index, "name": export["ObjectName"], "class": cls, "properties": fields})
        if cls == "Function":
            hooks.append({"export": index, "name": export["ObjectName"],
                          "script_bytes": export.get("ScriptBytecodeSize")})
        for p in export.get("LoadedProperties", []):
            if p.get("SerializedType") == "ObjectProperty":
                typed.append({"owner_export": index, "name": p["Name"],
                              "class": resolve(p.get("PropertyClass", 0))})
    names = obj["NameMap"]
    return {"source": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(data).hexdigest(),
            "exports": len(exports), "widgets_and_defaults": tree, "typed_properties": typed,
            "function_hooks": hooks,
            "culture_language_names": [s for s in names if "culture" in s.lower() or "language" in s.lower()],
            "switcher_widgets": [x for x in tree if "Switcher" in str(x["class"])],
            "ordinary_text_widgets": [x for x in tree if x["class"] in {"TextBlock", "RichTextBlock"}],
            "scope_note": "Serialized data and bytecode names in these two exports only; inherited native behavior is not ruled out"}


def main():
    sources = [ROOT / ("reports/rtl_research/" + name + ".json")
               for name in ["WBP_SubtitleBlock", "WBP_SubtitlesWidget"]]
    evidence = [inspect(p) for p in sources]
    block = evidence[0]
    assert block["exports"] == 37 and evidence[1]["exports"] == 43
    assert not any(e["switcher_widgets"] or e["ordinary_text_widgets"] or e["culture_language_names"] for e in evidence)
    text = [p for p in block["typed_properties"] if p["name"] in {"SubtitleProtoText", "SubtitleShadowProtoText"}]
    assert len(text) == 2 and all(p["class"] == "ProtoRichTextBlock" for p in text)
    result = {"branch_classification": "ARABIC_BRANCH_REQUIRES_NATIVE_INTEGRATION",
              "secondary_requirement": "ARABIC_BRANCH_REQUIRES_BLUEPRINT_CODE_CHANGE",
              "asset_only_branch_proven": False, "evidence_class": "CONFIRMED_FROM_ASSET",
              "classification_note": "Preferred new native renderer also needs explicit routing changes; no ready branch found",
              "assets": evidence}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "integration_points.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "assets"}, indent=2))


if __name__ == "__main__":
    main()
