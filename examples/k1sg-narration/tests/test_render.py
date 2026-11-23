"""Smoke tests for the K1SG local VoiceStudio CLI integration (no model needed)."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main, mock
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / "render.py"
SPEC = importlib.util.spec_from_file_location("k1sg_renderer", SCRIPT)
render_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render_module)


def settings(fmt="wav", overwrite=False):
    return SimpleNamespace(
        voice="K1SG Documentary", engine=None, speed=0.94,
        format=fmt, overwrite=overwrite,
    )


class RenderTests(TestCase):
    def test_milestone_filename_bounds(self):
        accepted = ["M-001.txt", "M-025.txt", "M-099.txt", "M-100.txt"]
        rejected = ["M-000.txt", "M-101.txt", "M-999.txt", "sample.txt"]
        for name in accepted:
            self.assertTrue(render_module.NAME.fullmatch(name), name)
        for name in rejected:
            self.assertFalse(render_module.NAME.fullmatch(name), name)

    def test_wav_uses_actual_voicestudio_cli_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "M-001.txt"
            source.write_text("Welcome to milestone one.", encoding="utf-8")
            output_dir = Path(tmp) / "out"
            calls = []

            def fake_run(command):
                calls.append(command)
                Path(command[command.index("--output") + 1]).write_bytes(b"RIFF" + b"\0" * 40)

            with mock.patch.object(render_module, "run", side_effect=fake_run):
                render_module.render(source, output_dir, settings())
            self.assertEqual(len(calls), 1)
            cmd = calls[0]
            self.assertEqual(cmd[:2], ["voicestudio", "speak"])
            self.assertEqual(cmd[cmd.index("--text-file") + 1], str(source))
            self.assertEqual(cmd[cmd.index("--voice") + 1], "K1SG Documentary")
            self.assertEqual(cmd[cmd.index("--speed") + 1], "0.94")
            self.assertIn("--instruct", cmd)
            self.assertTrue((output_dir / "M-001_VoiceStudio.wav").exists())

    def test_mp3_transcoding_is_invoked_after_voicestudio(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "M-001.txt"
            source.write_text("A resilient planetary grid.", encoding="utf-8")
            output = Path(tmp) / "out"
            calls = []

            def fake_run(command):
                calls.append(command)
                if command[0] == "voicestudio":
                    dest = Path(command[command.index("--output") + 1])
                else:
                    dest = Path(command[-1])
                dest.write_bytes(b"nonempty test fixture")

            with mock.patch.object(render_module, "run", side_effect=fake_run):
                render_module.render(source, output, settings("mp3"))
            self.assertEqual([c[0] for c in calls], ["voicestudio", "ffmpeg"])
            self.assertEqual(calls[1][calls[1].index("-b:a") + 1], "192k")
            self.assertTrue((output / "M-001_VoiceStudio.mp3").is_file())

    def test_refuses_overwrite_without_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "M-001.txt"
            source.write_text("Existing recording.", encoding="utf-8")
            output = Path(tmp) / "out"
            output.mkdir()
            (output / "M-001_VoiceStudio.wav").write_bytes(b"existing")
            with self.assertRaisesRegex(SystemExit, "Output exists"):
                render_module.render(source, output, settings())

    def test_rejects_empty_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "M-001.txt"
            source.write_text(" \n ", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "empty text script"):
                render_module.render(source, Path(tmp) / "out", settings())


if __name__ == "__main__":
    main()
