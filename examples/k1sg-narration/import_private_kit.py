#!/usr/bin/env python3
"""Stage K1SG narration scripts from a private production ZIP.

Reads only scripts_clean/M-001.txt .. M-100.txt and writes them to a
Git-ignored private_scripts directory. Does not run a voice model,
upload content, or interact with any remote service.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys
from zipfile import BadZipFile, ZipFile

DEST = Path(__file__).resolve().parent / "private_scripts"
NAME = re.compile(r"M-(?:0(?:0[1-9]|[1-9][0-9])|100)\.txt\Z")


def read_scripts(archive: ZipFile) -> dict[int, bytes]:
    found: dict[int, bytes] = {}
    for item in archive.infolist():
        if item.is_dir():
            continue
        segments = item.filename.split("/")
        if len(segments) < 2 or segments[-2] != "scripts_clean":
            continue
        filename = segments[-1]
        if not NAME.fullmatch(filename):
            continue
        number = int(filename[2:5])
        if number in found:
            raise ValueError(f"Duplicate M-{number:03d} in archive")
        if item.file_size > 100_000:
            raise ValueError(f"Script M-{number:03d} exceeds size limit")
        data = archive.read(item)
        if len(data) != item.file_size or not data.strip():
            raise ValueError(f"Empty or incomplete M-{number:03d}")
        try:
            data.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError(f"Script M-{number:03d} is not UTF-8") from exc
        found[number] = data
    return found


def stage(kit: Path, dest: Path, first: int, last: int,
          *, overwrite: bool = False) -> list[Path]:
    if not kit.is_file():
        raise ValueError(f"Production kit not found: {kit}")
    if not 1 <= first <= last <= 100:
        raise ValueError("Milestone range must lie between 1 and 100")
    try:
        with ZipFile(kit) as z:
            found = read_scripts(z)
    except BadZipFile as exc:
        raise ValueError("Invalid production ZIP") from exc
    requested = range(first, last + 1)
    missing = [i for i in requested if i not in found]
    if missing:
        raise ValueError("Missing scripts: " + ", ".join(f"M-{i:03d}" for i in missing))
    names = [dest / f"M-{n:03d}.txt" for n in requested]
    existing = [path for path in names if path.exists()]
    if existing and not overwrite:
        raise ValueError("Refusing to overwrite private scripts: " +
                         ", ".join(p.name for p in existing))
    dest.mkdir(parents=True, exist_ok=True)
    # Preflight passes before any file is written.
    for n, path in zip(requested, names):
        path.write_bytes(found[n])
    return names


def main() -> int:
    p = argparse.ArgumentParser(description="Import private Dyson K1 scripts for local VoiceStudio narration")
    p.add_argument("--kit", type=Path, required=True, help="Path to K1SG_VoiceStudio_Repo_Kit.zip")
    p.add_argument("--dest", type=Path, default=DEST, help="Local private_scripts destination")
    p.add_argument("--first", type=int, default=1)
    p.add_argument("--last", type=int, default=10, help="First batch is M-001 through M-010")
    p.add_argument("--all", action="store_true", help="Stage M-001 through M-100")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    first, last = (1, 100) if args.all else (args.first, args.last)
    try:
        staged = stage(args.kit.expanduser(), args.dest.expanduser(), first, last,
                       overwrite=args.overwrite)
    except (ValueError, OSError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(f"Staged {len(staged)} private scripts, M-{first:03d} through M-{last:03d}.")
    print("Output: " + str(args.dest.expanduser().resolve()))
    print("No scripts or audio were uploaded or committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
