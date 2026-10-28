"""Decode cooked UE4.27 Texture2D mips from extracted copies for text-bearing image inventory.

python -X utf8 tools/coverage/texture_probe.py <folder of extracted Dispatch/** textures> <thumb dir> [--ocr]

Reads FTexturePlatformData after the PF_* pixel-format string in each .uexp, takes the largest mip whose
payload is present (inline or in the .ubulk), decodes BC1/BC3/BC4/BC7/BGRA8/G8 with texture2ddecoder, and
writes a <=512px PNG thumbnail. --ocr runs the installed RapidOCR on the decoded image (targeted use only).
Never reads the game installation directly; give it a folder of extracted copies.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct
import sys

import numpy as np
from PIL import Image
import texture2ddecoder as t2d

ROOT = Path(__file__).resolve().parents[2]
PF = re.compile(rb"([\x05-\x20])\x00\x00\x00(PF_[A-Za-z0-9_]+)\x00")


def parse(uexp: bytes, ubulk: bytes | None):
    m = PF.search(uexp)
    if not m:
        return None
    fmt = m[2].decode()
    size_x, size_y = struct.unpack_from("<ii", uexp, m.start() - 12)
    pos = m.end()
    pos += 4  # FirstMipToSerialize
    (num_mips,) = struct.unpack_from("<i", uexp, pos)
    pos += 4
    mips = []
    for _ in range(num_mips):
        pos += 4  # bCooked
        flags, = struct.unpack_from("<I", uexp, pos)
        pos += 4
        if flags & 0x2000:  # BULKDATA_Size64Bit
            count, disk = struct.unpack_from("<qq", uexp, pos)
            pos += 16
        else:
            count, disk = struct.unpack_from("<ii", uexp, pos)
            pos += 8
        (offset,) = struct.unpack_from("<q", uexp, pos)
        pos += 8
        data = None
        if flags & 0x20 or disk <= 0:  # BULKDATA_Unused
            pass
        elif flags & 0x100:  # payload in separate .ubulk
            if ubulk is not None and offset + disk <= len(ubulk):
                data = ubulk[offset:offset + disk]
        else:
            data = uexp[pos:pos + disk]
            pos += disk
        w, h, d = struct.unpack_from("<iii", uexp, pos)
        pos += 12
        mips.append((w, h, data))
    return fmt, size_x, size_y, mips


def decode(fmt, w, h, data):
    if fmt == "PF_DXT1":
        raw = t2d.decode_bc1(data, w, h)
    elif fmt == "PF_DXT5":
        raw = t2d.decode_bc3(data, w, h)
    elif fmt == "PF_BC7":
        raw = t2d.decode_bc7(data, w, h)
    elif fmt == "PF_BC4":
        raw = t2d.decode_bc4(data, w, h)
    elif fmt == "PF_B8G8R8A8":
        raw = data[:w * h * 4]
    elif fmt == "PF_G8":
        return Image.frombytes("L", (w, h), data[:w * h]).convert("RGB")
    else:
        return None
    return Image.frombytes("RGBA", (w, h), raw, "raw", "BGRA")


def probe(path: Path, thumbs: Path, base: Path, ocr=None):
    uexp = path.with_suffix(".uexp").read_bytes()
    ubulk = path.with_suffix(".ubulk").read_bytes() if path.with_suffix(".ubulk").exists() else None
    parsed = parse(uexp, ubulk)
    rel = path.relative_to(base).as_posix()
    if not parsed:
        return {"asset": rel, "decoded": False, "reason": "no PF_ platform data"}
    fmt, sx, sy, mips = parsed
    usable = [(w, h, d) for w, h, d in mips if d is not None and w <= 8192 and h <= 8192]
    record = {"asset": rel, "format": fmt, "width": sx, "height": sy, "mips": len(mips)}
    if not usable:
        return {**record, "decoded": False, "reason": "no payload mip <=8192 present"}
    w, h, data = usable[0]
    try:
        image = decode(fmt, w, h, data)
    except Exception as error:  # decoder rejects truncated/odd payloads
        return {**record, "decoded": False, "reason": f"decode error: {error}"}
    if image is None:
        return {**record, "decoded": False, "reason": "unsupported format"}
    rgb = Image.alpha_composite(Image.new("RGBA", image.size, (40, 40, 40, 255)), image.convert("RGBA")).convert("RGB")
    thumb = rgb.copy()
    thumb.thumbnail((512, 512))
    out = thumbs / (rel.replace("/", "__") + ".png")
    thumb.save(out)
    record.update(decoded=True, decoded_mip=[w, h], thumbnail=out.name)
    if ocr is not None:
        result, _ = ocr(np.array(rgb if max(rgb.size) <= 1600 else thumb))
        record["ocr"] = [{"text": t, "score": round(float(s), 3)} for _, t, s in (result or []) if float(s) >= 0.6]
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("thumbs", type=Path)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--filter", default="", help="regex on asset path; only matching textures are probed")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    folder = args.folder.resolve()
    if "steamapps" in str(folder).lower():
        raise SystemExit("Probe extracted copies only")
    args.thumbs.mkdir(parents=True, exist_ok=True)
    ocr = None
    if args.ocr:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
    pattern = re.compile(args.filter) if args.filter else None
    records = []
    for path in sorted(folder.rglob("T_*.uasset")):
        rel = path.relative_to(folder).as_posix()
        if pattern and not pattern.search(rel):
            continue
        records.append(probe(path, args.thumbs, folder, ocr))
        print(len(records), rel, file=sys.stderr, flush=True) if len(records) % 50 == 0 else None
    args.out.write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"probed": len(records), "decoded": sum(r.get("decoded", False) for r in records),
                      "with_ocr_text": sum(bool(r.get("ocr")) for r in records)}))


if __name__ == "__main__":
    main()
