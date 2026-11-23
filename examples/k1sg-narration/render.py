#!/usr/bin/env python3
"""Local K1SG narration using VoiceStudio's own CLI; no third-party TTS."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
NAME = re.compile(r"M-(?:0[0-9]{2}|100)\.txt\Z", re.IGNORECASE)

def run(cmd):
    outcome = subprocess.run(cmd, check=False)
    if outcome.returncode:
        raise SystemExit("Command failed: " + cmd[0])

def render(src, dest, args):
    if not src.is_file() or not src.read_text(encoding="utf-8").strip():
        raise SystemExit("Missing or empty text script: " + str(src))
    dest.mkdir(parents=True, exist_ok=True)
    wav = dest / (src.stem + "_VoiceStudio.wav")
    target = dest / (src.stem + "_VoiceStudio." + args.format)
    if target.exists() and not args.overwrite:
        raise SystemExit("Output exists; pass --overwrite: " + str(target))
    if args.format == "mp3" and wav.exists() and not args.overwrite:
        raise SystemExit("Intermediate WAV exists; pass --overwrite: " + str(wav))
    command = ["voicestudio", "speak", "--text-file", str(src),
               "--voice", args.voice, "--language", "en",
               "--speed", str(args.speed), "--instruct",
               "Read as a warm, resonant science documentary narrator. "
               "Precise scientific diction, unhurried delivery, natural pauses, "
               "restrained wonder, never a sales announcer.",
               "--output", str(wav)]
    if args.engine:
        command.extend(["--engine", args.engine])
    if args.overwrite:
        command.append("--overwrite")
    run(command)
    if not wav.is_file() or wav.stat().st_size == 0:
        raise SystemExit("VoiceStudio did not produce a nonempty WAV file.")
    if args.format == "mp3":
        run(["ffmpeg", "-y" if args.overwrite else "-n", "-hide_banner",
             "-loglevel", "error", "-i", str(wav),
             "-af", "loudnorm=I=-17:TP=-1.5:LRA=11",
             "-codec:a", "libmp3lame", "-b:a", "192k", str(target)])
        if not target.is_file() or target.stat().st_size == 0:
            raise SystemExit("MP3 encoding failed.")
    print("Rendered:", target)

def main():
    p = argparse.ArgumentParser(description="Render K1SG science narration locally with VoiceStudio")
    p.add_argument("--input-dir", type=Path, default=ROOT / "private_scripts")
    p.add_argument("--output-dir", type=Path, default=ROOT / "private_output")
    p.add_argument("--milestone", default="M-001")
    p.add_argument("--all", action="store_true")
    p.add_argument("--voice", default=os.getenv("K1SG_VOICE", "K1SG Documentary"))
    p.add_argument("--engine")
    p.add_argument("--speed", type=float, default=0.94)
    p.add_argument("--format", choices=["wav", "mp3"], default="mp3")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    if not 0.5 <= args.speed <= 1.5:
        p.error("--speed must be between 0.5 and 1.5")
    if not args.voice.strip():
        p.error("--voice must be a saved VoiceStudio profile")
    if not shutil.which("voicestudio"):
        raise SystemExit("VoiceStudio CLI missing. Install/start the upstream application.")
    if args.format == "mp3" and not shutil.which("ffmpeg"):
        raise SystemExit("MP3 output requires ffmpeg; use --format wav otherwise.")
    source = args.input_dir.expanduser().resolve()
    output = args.output_dir.expanduser().resolve()
    if args.all:
        scripts = sorted(f for f in source.iterdir()
                         if f.is_file() and NAME.fullmatch(f.name)) if source.is_dir() else []
        if not scripts:
            raise SystemExit("No M-###.txt files found: " + str(source))
    else:
        milestone = args.milestone.upper()
        if not NAME.fullmatch(milestone + ".txt"):
            p.error("--milestone must be M-001 through M-100")
        scripts = [source / (milestone + ".txt")]
    for src in scripts:
        render(src, output, args)

if __name__ == "__main__":
    main()
