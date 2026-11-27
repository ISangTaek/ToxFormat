import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("toxformat_installer", ROOT / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTest(unittest.TestCase):
    def test_migrate_without_destroying_old_skill_or_custom_files(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            skills = home / "skills"
            legacy = skills / "gzh-design"
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text("---\nname: gzh-design\n---\n", encoding="utf-8")
            (legacy / "private-theme.md").write_bytes(b"my theme")
            with self.assertRaises(ValueError):
                installer.install(skills)
            installed, backup = installer.install(skills, migrate=True)
            self.assertEqual([p.parent.name for p in skills.rglob("SKILL.md")], ["toxformat"])
            self.assertFalse(backup.is_relative_to(skills))
            self.assertEqual((backup / "gzh-design/private-theme.md").read_bytes(), b"my theme")
            self.assertEqual(installer.inventory(installed), installer.inventory(ROOT / "toxformat"))
            self.assertIsNone(installer.install(skills, migrate=True)[1])
            (installed / "editor-resource.md").write_text("编辑自加资料", encoding="utf-8")
            _, previous = installer.install(skills, migrate=True)
            self.assertTrue((previous / "toxformat/editor-resource.md").is_file())
