"""Summarize inspector JSON without changing assets or the exported JSON."""
import json
import sys
from pathlib import Path


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


for filename in sys.argv[1:]:
    asset = json.loads(Path(filename).read_text(encoding="utf-8"))
    imports = asset.get("Imports", [])
    exports = asset.get("Exports", [])

    def resolve(index):
        if index < 0:
            item = imports[-index - 1]
        elif index > 0:
            item = exports[index - 1]
        else:
            return "None"
        outer = item.get("OuterIndex", 0)
        return (resolve(outer) + ":" if outer else "") + item["ObjectName"]

    print("ASSET", filename)
    for index, export in enumerate(exports, 1):
        print("EXPORT", index, export["ObjectName"], resolve(export.get("ClassIndex", 0)))
        if "Data" in export:
            for prop in export["Data"]:
                print(" PROPERTY", prop.get("Name"), json.dumps(prop.get("Value", prop.get("EnumValue")), ensure_ascii=False))
        for row in export.get("Table", {}).get("Data", []):
            fields = {}
            for node in walk(row.get("Value", [])):
                name = node.get("Name", "")
                if name in {"FontObject", "FontMaterial", "OutlineMaterial"}:
                    fields[name] = resolve(node["Value"])
                elif name in {"TypefaceFontName", "Size", "PrintLetterAnimationTime", "PrintLetterInterval", "UseAdvancedPrintIntervals"}:
                    fields[name] = node.get("Value")
            print(" STYLE", row["Name"], json.dumps(fields, ensure_ascii=False))
        for node in walk(export.get("ScriptBytecode", [])):
            if "VirtualFunctionName" in node:
                print(" CALL", node["VirtualFunctionName"])
            if "StackNode" in node:
                print(" CALL", resolve(node["StackNode"]))
            if node.get("$type", "").split(",")[0].endswith(("EX_StringConst", "EX_UnicodeStringConst", "EX_TextConst", "EX_FloatConst")):
                print(" LITERAL", json.dumps(node, ensure_ascii=False))
            if node.get("$type", "").split(",")[0].endswith("EX_InstanceVariable"):
                print(" INSTANCE", node.get("Variable", {}).get("New", {}).get("Path"))
