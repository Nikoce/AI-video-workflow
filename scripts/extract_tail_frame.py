#!/usr/bin/env python3
"""Extract an actual tail frame from an accepted video segment."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_executable(explicit: str | None, name: str, required: bool) -> str | None:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Executable not found: {path}")
        return str(path)
    found = shutil.which(name)
    if required and not found:
        raise FileNotFoundError(f"{name} was not found; pass --{name} or add it to PATH.")
    return found


def get_duration(path: Path, ffprobe: str | None) -> float | None:
    if not ffprobe:
        return None
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        return None
    try:
        return round(float(completed.stdout.strip()), 3)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Accepted video segment path")
    parser.add_argument("output", help="Output .png, .jpg, .jpeg, or .webp path")
    parser.add_argument("--offset", type=float, default=0.1, help="Seconds before the end")
    parser.add_argument("--ffmpeg", help="Explicit ffmpeg executable path")
    parser.add_argument("--ffprobe", help="Explicit ffprobe executable path")
    parser.add_argument("--force", action="store_true", help="Replace an existing output")
    args = parser.parse_args()

    if not 0.01 <= args.offset <= 2.0:
        parser.error("--offset must be between 0.01 and 2.0 seconds.")

    video = Path(args.path).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not video.is_file():
        parser.error(f"Video segment does not exist: {video}")
    if output.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        parser.error("Output must use .png, .jpg, .jpeg, or .webp.")
    if output.exists() and not args.force:
        parser.error(f"Output exists; pass --force to replace it: {output}")

    ffmpeg = resolve_executable(args.ffmpeg, "ffmpeg", required=True)
    ffprobe = resolve_executable(args.ffprobe, "ffprobe", required=False)
    if not ffprobe and ffmpeg:
        sibling = Path(ffmpeg).with_name("ffprobe.exe" if Path(ffmpeg).suffix.lower() == ".exe" else "ffprobe")
        if sibling.is_file():
            ffprobe = str(sibling)

    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-sseof",
        f"-{args.offset:g}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-y" if args.force else "-n",
        str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0 or not output.is_file():
        raise RuntimeError(completed.stderr.strip() or "ffmpeg did not create the tail frame.")

    duration = get_duration(video, ffprobe)
    timestamp = round(max(0.0, duration - args.offset), 3) if duration is not None else None
    result = {
        "schema_version": 1,
        "source_video_path": str(video),
        "source_video_sha256": sha256_file(video),
        "duration_seconds": duration,
        "offset_from_end_seconds": args.offset,
        "tail_frame_timestamp_seconds": timestamp,
        "tail_frame_path": str(output),
        "tail_frame_size_bytes": output.stat().st_size,
        "tail_frame_sha256": sha256_file(output),
        "requires_visual_review": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
