# K1SG × VoiceStudio — local narration sample

This example uses the open-source VoiceStudio CLI from this fork. It does **not** call ElevenLabs or Higgsfield. User-authored Dyson Ascension scripts and produced audio are deliberately excluded from this public repository.

## Local prerequisites

1. Install and start VoiceStudio from this repository, following its upstream README. Make sure the `voicestudio` executable is on your PATH.
2. Run `voicestudio status` and `voicestudio models list`; install a compatible TTS model through the app.
3. **Review the engine, model-weight and voice-asset licenses individually** before commercial narration. App source licensing does not automatically grant commercial rights to every model.
4. Run `voicestudio voices list`. Create/select a local voice profile, preferably a calm, articulate documentary-style male narrator. The default script profile name `K1SG Documentary` must actually exist.
5. Install `ffmpeg` for MP3 output (or choose WAV). Python 3.9+ is sufficient for this runner.

## Test M-001

Copy the prepared TTS-clean `M-001.txt` from your private K1SG production kit to `examples/k1sg-narration/private_scripts/M-001.txt`. This private folder is Git-ignored. Some original source scripts use delivery tags like `[pause]`; if your engine doesn't support them, use the cleaned copy to avoid reading tags aloud.

From the repository root, use:

    python3 examples/k1sg-narration/render.py --milestone M-001 --voice "K1SG Documentary" --format wav

For MP3:

    python3 examples/k1sg-narration/render.py --milestone M-001 --voice "K1SG Documentary" --format mp3

The output is placed in `examples/k1sg-narration/private_output/`. The runner only reports success after VoiceStudio produces a nonempty WAV file, and checks MP3 encoding when requested.

Use `--voice` to select any existing local profile; `--engine` can override the installed TTS engine ID; and `--speed` changes narration speed (default 0.94). To regenerate an existing output, use `--overwrite`.

## Batch K1 milestones

Once M-001 is approved, copy the other cleaned `M-###.txt` scripts to the same ignored `private_scripts/` folder and run:

    python3 examples/k1sg-narration/render.py --all --voice "K1SG Documentary" --format mp3

## Scope

This is an integration example, **not a completed neural audio sample or an installed backend**. The real VoiceStudio model and voice profile must run on a compatible machine. No GitHub Action attempts synthesis: remote CI does not automatically have the model weights, license approvals, voice profile, or the private K1SG content. Never commit the private script folder to this public fork.
