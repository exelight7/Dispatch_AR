"""Trace every OtherContent identity that is in the manifest but absent from the shipped English locres.

python -X utf8 tools/coverage/othercontent_trace.py [--asset-registry PATH]
Reads reports/manifest_only_keys.json, the pak path index and (optionally) a temporary copy of the
shipped Dispatch/AssetRegistry.bin. Writes reports/coverage/othercontent_manifest_only.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from localization import read_locres  # noqa: E402

LOCRES = ROOT / "extracted/Dispatch/Content/Localization/OtherContent/en/OtherContent.locres"


def package_file(context):
    package = context.split(":")[0].split(".")[0]
    return package, "Dispatch/Content/" + package[len("/Game/"):] + ".uasset"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-registry", type=Path)
    args = parser.parse_args()
    rows = json.loads((ROOT / "reports/manifest_only_keys.json").read_text(encoding="utf-8"))
    indexed = {e["path"] for e in json.loads((ROOT / "reports/all_asset_paths.json").read_text(encoding="utf-8"))}
    registry = args.asset_registry.read_bytes() if args.asset_registry else None
    shipped = {(r["namespace"], r["key"]) for r in read_locres(LOCRES.read_bytes())["rows"]}
    out = []
    for row in rows:
        package, file = package_file(row["context"])
        in_pak = file in indexed
        in_registry = None if registry is None else package.encode() in registry
        assert (row["namespace"], row["key"]) not in shipped
        if in_pak or in_registry:
            label, reason, action = "UNRESOLVED", "Owning package is shipped; locres absence unexplained.", "Investigate"
        else:
            label = "SOURCE_ONLY"
            reason = ("Owning editor-utility widget package is absent from all 20 pak indexes"
                      + ("" if registry is None else " and from the shipped AssetRegistry.bin")
                      + "; the text exists only in the developer's source manifest and cannot be loaded at runtime.")
            action = "No translation; excluded from runtime scope (developer censor-authoring tool UI)."
        out.append({"namespace": row["namespace"], "key": row["key"], "en": row["en"],
                    "manifest_location": "Dispatch/Content/Localization/OtherContent/OtherContent.manifest",
                    "manifest_context": row["context"], "expected_locres": "Dispatch/Content/Localization/OtherContent/en/OtherContent.locres",
                    "package": package, "package_file_in_pak_index": in_pak, "package_in_asset_registry": in_registry,
                    "classification": label, "reason_for_locres_absence": reason,
                    "runtime_relevance": "NONE" if label == "SOURCE_ONLY" else "UNKNOWN", "action": action})
    dest = ROOT / "reports/coverage/othercontent_manifest_only.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {}
    for r in out:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    print(json.dumps({"records": len(out), "classes": counts,
                      "packages": sorted({r["package"] for r in out})}, indent=2))


if __name__ == "__main__":
    main()
