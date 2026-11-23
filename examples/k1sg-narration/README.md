# K1SG × VoiceStudio — local narration sample

This example uses the open-source VoiceStudio CLI from this fork. It does **not** call ElevenLabs or Higgsfield. User-authored Dyson Ascension scripts and produced audio are deliberately excluded from this public repository.

## Local prerequisites

1. Install and start VoiceStudio from this repository, following its upstream README. Make sure the `voicestudio` executable is on your PATH.
2. Run `voicestudio status` and `voicestudio models list`; install a compatible TTS model through the app.
3. **Review the engine, model-weight and voice-asset licenses individually** before commercial narration. App source licensing does not automatically grant commercial rights to every model.
4. Run `voicestudio voices list`. Create/select a local voice profile, preferably a calm, articulate documentary-style male narrator. The default script profile name `K1SG Documentary` must actually exist.
5. Install `ffmpeg` for MP3 output (or choose WAV). Python 3.11+ is required for the VoiceStudio CLI (see `cli/pyproject.toml`).

## Quick start from your fork (Linux/macOS + Docker)

Run these commands on **your own computer**, not in the GitHub mobile app. They start the official upstream VoiceStudio CPU container and use the CLI from this fork. They do not download or accept any model licence automatically.

```bash
git clone https://github.com/singlekm/voicestudio.git
cd voicestudio
git switch feature/k1sg-narration-cli

# Python 3.11+ and Docker must already be installed
python3 -m venv .k1sg-venv
. .k1sg-venv/bin/activate
python -m pip install -e ./cli

export OMNIVOICE_API_KEY="$(openssl rand -hex 32)"
docker run -d --name k1sg-voicestudio \
  -p 127.0.0.1:3900:3900 \
  -e OMNIVOICE_API_KEY \
  -e OMNIVOICE_DATA_DIR=/app/omnivoice_data \
  -v k1sg-voicestudio-data:/app/omnivoice_data \
  ghcr.io/debpalash/voicestudio:stable

voicestudio connection set http://127.0.0.1:3900
printf '%s' "$OMNIVOICE_API_KEY" | voicestudio connection auth set --stdin
voicestudio connection test
voicestudio models list
voicestudio voices list
```

Do **not** commit the generated API key, downloaded model files, user-authored scripts, or rendered audio. The API binds to localhost only. The Docker image can take substantial disk space and CPU time.

Then visit `http://localhost:3900` on that computer, install a model supported by the CPU backend, review and accept its licensing terms yourself, and set up the `K1SG Documentary` voice profile. Verify model and voice readiness with `voicestudio models list` and `voicestudio voices list`, then run the M-001 command below. Refer to the upstream [Docker guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/docker.md) for OS-specific setup and GPU acceleration.

For an existing local desktop installation, skip Docker and use the application's own configured backend.

## Import your private 100-script production kit

Keep `K1SG_VoiceStudio_Repo_Kit.zip` on your computer. It contains the prepared narration text and is **not** committed to GitHub.

To stage the first 10 scripts without manually copying files:

```bash
python3 examples/k1sg-narration/import_private_kit.py \
  --kit /path/to/K1SG_VoiceStudio_Repo_Kit.zip
```

That stages M-001 through M-010 into the Git-ignored `private_scripts/` folder. To stage just M-001, add `--first 1 --last 1`; after audition approval, stage all 100 with `--all`. The importer refuses to overwrite existing files unless you explicitly pass `--overwrite`, validates the requested script range and UTF-8 text, and never uploads the contents.

## Windows one-command M-001 pilot

On **Windows PowerShell**, install/start VoiceStudio on your PC first. The official desktop release or the Docker quickstart above provides the backend; the runner uses its local CLI. Install Python 3.11+ and FFmpeg for MP3 output. With the fork checked out to this feature branch:

```powershell
python -m pip install -e ./cli
python examples/k1sg-narration/preflight.py --milestone M-001

# When your local model, backend and saved narrator profile are ready:
./examples/k1sg-narration/run_pilot_windows.ps1 -Kit "C:\Users\YOU\Downloads\K1SG_VoiceStudio_Repo_Kit.zip"
```

The PowerShell command stages **only M-001**, validates the private local input and your saved voice profile, and calls the real VoiceStudio CLI to produce `private_output/M-001_VoiceStudio.mp3`. It never publishes scripts or output. The `-Voice`, `-Milestone`, `-Format`, `-Engine`, `-Python` and `-Overwrite` options are optional. If using `-Overwrite`, expect it to overwrite both the staged private input and rendered output. Do not change your computer's global PowerShell execution policy; use an appropriate per-process policy only if your organization allows script execution.

This script **does not install or select a model, accept licence terms, or create a voice profile for you**. Those are required before it can generate audio.

## Check readiness before spending time on a render

After selecting a model and saved voice, copy `M-001.txt` to the ignored `private_scripts/` directory, then run:

```bash
python3 examples/k1sg-narration/preflight.py --milestone M-001 --voice "K1SG Documentary"
```

The preflight checks the VoiceStudio CLI, authenticated backend connection, existence of at least one installed model, the exact saved voice profile, the local private text file, and FFmpeg for MP3. It does not synthesize audio, accept licences, show secrets, or expose narration scripts. A successful preflight is **not** evidence that the installed model supports your chosen voice or commercial use: run the audition and review licensing separately.

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

## Repeatable checks in GitHub Actions

The `K1SG VoiceStudio CLI smoke tests` workflow runs automatically for changes to this directory. It validates the exact CLI argument construction, milestone numbering, nonempty WAV output checks, optional MP3 conversion, and overwrite protections using isolated test doubles. **It does not synthesize audio** or retrieve the private scripts.

Locally, run:

    python3 -m unittest discover -s examples/k1sg-narration/tests -v

Once VoiceStudio is installed and has a commercially permitted, compatible TTS model and saved voice profile, run the M-001 command above on that computer. An actual audio audition is required before this PR should be regarded as production-ready.
