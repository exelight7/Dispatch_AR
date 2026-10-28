"""Probe extracted copies of Dispatch movies for subtitle streams and burned-in text (sample-based).

python -X utf8 tools/coverage/video_probe.py <folder of extracted Movies copies> <frame dir> --out <json> [--every 5] [--ocr]

Uses the ffmpeg binary bundled with the installed imageio-ffmpeg: lists streams (a subtitle stream
would appear as 'Subtitle:'), grabs one frame every N seconds, and optionally runs RapidOCR on them.
Never transcodes or writes movies; never reads the game installation directly.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def streams(path):
    info = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True, errors="replace").stderr
    duration = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
    seconds = int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3]) if duration else 0.0
    kinds = re.findall(r"Stream #\d+:\d+(?:\[[^\]]*\])?(?:\(\w+\))?: (Video|Audio|Subtitle|Data|Attachment): ([^\n]*)", info)
    return seconds, [{"type": k, "codec": v.split(",")[0].strip()} for k, v in kinds]


def frames(path, every, dest):
    dest.mkdir(parents=True, exist_ok=True)
    pattern = dest / (path.stem + "_%04d.png")
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-i", str(path), "-vf", f"fps=1/{every},scale=960:-1",
                    str(pattern)], check=True)
    return sorted(dest.glob(path.stem + "_*.png"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("frames", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--every", type=float, default=5.0)
    parser.add_argument("--ocr", action="store_true")
    args = parser.parse_args()
    if "steamapps" in str(args.folder.resolve()).lower():
        raise SystemExit("Probe extracted copies only")
    ocr = None
    if args.ocr:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
    out = []
    for path in sorted(args.folder.rglob("*")):
        if path.suffix.lower() not in (".webm", ".mp4"):
            continue
        seconds, kinds = streams(path)
        record = {"movie": path.relative_to(args.folder).as_posix(), "bytes": path.stat().st_size,
                  "duration_s": round(seconds, 2), "streams": kinds,
                  "subtitle_streams": sum(k["type"] == "Subtitle" for k in kinds)}
        if ocr is not None:
            texts = []
            for frame in frames(path, args.every, args.frames):
                result, _ = ocr(np.array(Image.open(frame).convert("RGB")))
                found = [t for _, t, s in (result or []) if float(s) >= 0.7 and len(t.strip()) >= 3]
                if found:
                    texts.append({"frame": frame.name, "text": found[:12]})
            record["ocr_frames_with_text"] = len(texts)
            record["ocr_samples"] = texts[:6]
        out.append(record)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"movies": len(out), "with_subtitle_streams": sum(r["subtitle_streams"] > 0 for r in out),
                      "with_ocr_text": sum(bool(r.get("ocr_frames_with_text")) for r in out)}))


if __name__ == "__main__":
    main()
