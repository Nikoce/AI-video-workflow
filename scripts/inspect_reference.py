#!/usr/bin/env python3
"""Inspect a local reference video without uploading it."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_executable(explicit: str | None, name: str) -> str | None:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Executable not found: {path}")
        return str(path)
    return shutil.which(name)


def parse_rate(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        return round(float(Fraction(value)), 6)
    except (ValueError, ZeroDivisionError):
        return None


def parse_float(value: Any) -> float | None:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return None


def inspect_video(path: Path, ffprobe: str | None) -> dict[str, Any]:
    warnings: list[str] = []
    probe_data: dict[str, Any] = {}

    if ffprobe:
        command = [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if completed.returncode == 0:
            probe_data = json.loads(completed.stdout or "{}")
        else:
            warnings.append(f"ffprobe failed: {completed.stderr.strip() or 'unknown error'}")
    else:
        warnings.append("ffprobe was not found; media fields remain unknown.")

    streams = probe_data.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    media_format = probe_data.get("format", {})

    width = video.get("width")
    height = video.get("height")
    aspect_ratio = None
    orientation = "unknown"
    if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
        divisor = math.gcd(width, height)
        aspect_ratio = f"{width // divisor}:{height // divisor}"
        orientation = "landscape" if width > height else "portrait" if height > width else "square"
    else:
        warnings.append("Frame dimensions are unavailable.")

    duration = parse_float(media_format.get("duration") or video.get("duration"))
    if duration is None:
        warnings.append("Duration is unavailable.")

    return {
        "schema_version": 1,
        "file": {
            "path": str(path),
            "name": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        },
        "media": {
            "duration_seconds": duration,
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "orientation": orientation,
            "frame_rate": parse_rate(video.get("avg_frame_rate") or video.get("r_frame_rate")),
            "video_codec": video.get("codec_name"),
            "pixel_format": video.get("pix_fmt"),
            "has_audio": bool(audio),
            "audio_codec": audio.get("codec_name"),
            "sample_rate": parse_float(audio.get("sample_rate")),
        },
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Local reference video path")
    parser.add_argument("--ffprobe", help="Explicit ffprobe executable path")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    path = Path(args.path).expanduser().resolve()
    if not path.is_file():
        parser.error(f"Reference video does not exist: {path}")

    ffprobe = resolve_executable(args.ffprobe, "ffprobe")
    result = inspect_video(path, ffprobe)
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")

    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
