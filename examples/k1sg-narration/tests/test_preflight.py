"""Tests for local readiness checks without running a voice model."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main, mock

PATH = Path(__file__).resolve().parents[1] / "preflight.py"
SPEC = importlib.util.spec_from_file_location("k1sg_preflight", PATH)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class PreflightTests(TestCase):
    def test_reports_missing_cli_without_contacting_backend(self):
        with mock.patch.object(module.shutil, "which", return_value=None):
            ok, notes = module.check("K1SG Documentary", "M-001", Path("."), True)
        self.assertFalse(ok)
        self.assertIn("CLI not found", notes[0])

    def test_ready_when_backend_model_profile_script_and_ffmpeg_exist(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "M-001.txt").write_text("A full global grid.", encoding="utf-8")
            def response(*args):
                if args[:2] == ("connection", "test"):
                    return {"status": "ok"}
                if args[:2] == ("models", "list"):
                    return {"models": [{"repo_id": "approved-model"}]}
                return [{"id": "voice-1", "name": "K1SG Documentary"}]

            with mock.patch.object(module.shutil, "which", return_value="/usr/bin/tool"), \
                 mock.patch.object(module, "get_json", side_effect=response):
                ok, notes = module.check("K1SG Documentary", "M-001", p, True)
            self.assertTrue(ok, notes)
            self.assertIn("READY", notes[-1])

    def test_backend_not_ready_is_failure(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "M-001.txt").write_text("Another milestone.", encoding="utf-8")
            def response(*args):
                if args[:2] == ("connection", "test"):
                    return None
                if args[:2] == ("models", "list"):
                    return {"models": [{"repo_id": "installed"}]}
                return [{"name": "K1SG Documentary"}]
            with mock.patch.object(module.shutil, "which", return_value="/bin/tool"), \
                 mock.patch.object(module, "get_json", side_effect=response):
                ok, notes = module.check("K1SG Documentary", "M-001", p, False)
            self.assertFalse(ok)
            self.assertTrue(any("backend unavailable" in n for n in notes))

    def test_voice_not_found_is_failure(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "M-001.txt").write_text("Prepare to narrate.", encoding="utf-8")
            def response(*args):
                if args[:2] == ("connection", "test"):
                    return {"status": "ok"}
                if args[:2] == ("models", "list"):
                    return {"models": [{"repo_id": "installed"}]}
                return [{"name": "Another narrator"}]
            with mock.patch.object(module.shutil, "which", return_value="/bin/tool"), \
                 mock.patch.object(module, "get_json", side_effect=response):
                ok, notes = module.check("K1SG Documentary", "M-001", p, False)
            self.assertFalse(ok)
            self.assertTrue(any("voice profile not found" in n for n in notes))

    def test_invalid_json_returns_none_without_exposing_raw_output(self):
        result = mock.Mock(returncode=0, stdout="not-json")
        with mock.patch.object(module.subprocess, "run", return_value=result):
            self.assertIsNone(module.get_json("voices", "list"))
        result = mock.Mock(returncode=1, stdout="", stderr="SECRET=hidden")
        with mock.patch.object(module.subprocess, "run", return_value=result):
            self.assertIsNone(module.get_json("connection", "test"))


if __name__ == "__main__":
    main()
