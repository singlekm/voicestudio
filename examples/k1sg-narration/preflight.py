#!/usr/bin/env python3
"""Read-only readiness check for a LOCAL VoiceStudio K1SG narrator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def get_json(*args: str):
    """Call the documented VoiceStudio CLI without displaying credentials."""
    try:
        result = subprocess.run(
            ["voicestudio", *args, "--json"],
            capture_output=True, text=True, check=False, timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return None


def profiles_from(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("profiles", "voices", "data"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def check(voice: str, milestone: str, input_dir: Path, need_mp3: bool) -> tuple[bool, list[str]]:
    messages = []
    ok = True
    cli = shutil.which("voicestudio")
    if not cli:
        return False, ["FAIL: VoiceStudio CLI not found on PATH. Install VoiceStudio first."]
    messages.append("OK: VoiceStudio CLI available")
    # The locally selected connection and API key remain inside VoiceStudio's
    # own configuration; do not print or copy them.
    health = get_json("connection", "test")
    if health is None:
        ok = False
        messages.append("FAIL: VoiceStudio backend unavailable or unauthenticated. Run: voicestudio connection test")
    else:
        messages.append("OK: VoiceStudio backend connection responded")

    models = get_json("models", "list", "--installed")
    installed = models.get("models") if isinstance(models, dict) else None
    if not isinstance(installed, list) or not installed:
        ok = False
        messages.append("FAIL: No installed model found. Review the license and install a compatible TTS model.")
    else:
        messages.append("OK: At least one model installed; verify your chosen model is TTS-capable")

    voices = profiles_from(get_json("voices", "list"))
    found = any(isinstance(p, dict) and (p.get("name", "").casefold() == voice.casefold() or p.get("id") == voice) for p in voices)
    if not found:
        ok = False
        messages.append("FAIL: Narrator voice profile not found. Run: voicestudio voices list")
    else:
        messages.append("OK: Narrator voice profile found")

    text_path = input_dir / (milestone + ".txt")
    if not text_path.is_file() or not text_path.stat().st_size:
        ok = False
        messages.append("FAIL: Local private milestone script missing or empty: " + milestone)
    else:
        messages.append("OK: Private script exists: " + milestone)
    if need_mp3 and not shutil.which("ffmpeg"):
        ok = False
        messages.append("FAIL: ffmpeg is needed for MP3 output (or request WAV)")
    elif need_mp3:
        messages.append("OK: ffmpeg available")

    if ok:
        messages.append("READY for a local audition; quality and commercial licensing still require human review")
    else:
        messages.append("NOT READY: resolve the failures before generating narration")
    return ok, messages


def main():
    parser = argparse.ArgumentParser(description="Check local K1SG VoiceStudio narrator prerequisites")
    parser.add_argument("--voice", default="K1SG Documentary")
    parser.add_argument("--milestone", default="M-001")
    parser.add_argument("--input-dir", type=Path, default=Path(__file__).resolve().parent / "private_scripts")
    parser.add_argument("--format", choices=["wav", "mp3"], default="mp3")
    args = parser.parse_args()
    if not args.milestone.startswith("M-") or len(args.milestone) != 5 or not args.milestone[2:].isdigit() or not 1 <= int(args.milestone[2:]) <= 100:
        parser.error("--milestone must be M-001 through M-100")
    ok, notes = check(args.voice, args.milestone, args.input_dir.expanduser(), args.format == "mp3")
    print("\n".join(notes))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
