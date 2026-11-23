"""Tests that private K1SG scripts import securely without an audio service."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from zipfile import ZipFile

SCRIPT = Path(__file__).resolve().parents[1] / "import_private_kit.py"
SPEC = importlib.util.spec_from_file_location("k1sg_kit_import", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def make_zip(path, scripts):
    with ZipFile(path, "w") as z:
        for name, content in scripts.items():
            z.writestr(f"K1SG_VoiceStudio_Repo_Kit/scripts_clean/{name}", content)


class PrivateKitTests(TestCase):
    def test_stage_first_batch_only(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            zip_path = root / "kit.zip"
            scripts = {f"M-{n:03d}.txt": f"Episode {n}".encode() for n in range(1, 11)}
            scripts["README.txt"] = b"not a narration input"
            make_zip(zip_path, scripts)
            out = root / "private_scripts"
            items = module.stage(zip_path, out, 1, 10)
            self.assertEqual(len(items), 10)
            self.assertEqual((out / "M-001.txt").read_bytes(), b"Episode 1")
            self.assertFalse((out / "README.txt").exists())

    def test_no_partial_output_on_missing_script(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            z = root / "kit.zip"
            make_zip(z, {"M-001.txt": b"one"})
            out = root / "private_scripts"
            with self.assertRaisesRegex(ValueError, "Missing scripts"):
                module.stage(z, out, 1, 2)
            self.assertFalse(out.exists())

    def test_no_overwrite_by_default(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            z = root / "kit.zip"
            make_zip(z, {"M-001.txt": b"new"})
            out = root / "private_scripts"
            out.mkdir()
            (out / "M-001.txt").write_bytes(b"existing")
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                module.stage(z, out, 1, 1)
            self.assertEqual((out / "M-001.txt").read_bytes(), b"existing")

    def test_overwrite_with_explicit_option(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            z = root / "kit.zip"
            make_zip(z, {"M-001.txt": b"new"})
            out = root / "private_scripts"
            out.mkdir()
            (out / "M-001.txt").write_bytes(b"existing")
            module.stage(z, out, 1, 1, overwrite=True)
            self.assertEqual((out / "M-001.txt").read_bytes(), b"new")

    def test_reject_duplicate_members(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            z = root / "kit.zip"
            with ZipFile(z, "w") as archive:
                archive.writestr("a/scripts_clean/M-001.txt", "first")
                archive.writestr("b/scripts_clean/M-001.txt", "second")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                module.stage(z, root / "private_scripts", 1, 1)

    def test_reject_outside_milestone_range(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            z = root / "kit.zip"
            make_zip(z, {"M-000.txt": b"bad", "M-001.txt": b"one",
                         "M-101.txt": b"bad"})
            with self.assertRaisesRegex(ValueError, "Missing scripts"):
                module.stage(z, root / "private_scripts", 1, 2)
            with self.assertRaisesRegex(ValueError, "range"):
                module.stage(z, root / "private_scripts", 0, 10)

if __name__ == "__main__":
    main()
