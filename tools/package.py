"""Build deterministic ZIPs for direct skill import and for the complete portable project."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "toxformat/assets/catalog.json").read_text(encoding="utf-8"))["version"]


def members(paths):
    entries = []
    for path in paths:
        entries.extend(path.rglob("*") if path.is_dir() else [path])
    return sorted(
        p for p in entries if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )


def write_archive(path, files, skill_only=False):
    path.parent.mkdir(exist_ok=True)
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for item in files:
            name = item.relative_to(ROOT).as_posix()
            if skill_only and name.startswith("栏目头图与尾图/"):
                name = "toxformat/" + name
            info = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            data = item.read_bytes()
            if (
                item.suffix.lower()
                not in {".doc", ".docx", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}
                and b"\0" not in data
            ):
                data = data.replace(b"\r\n", b"\n")
            archive.writestr(info, data, compress_type=ZIP_DEFLATED)
    with ZipFile(path) as archive:
        if archive.testzip() or [n for n in archive.namelist() if n.endswith("/SKILL.md")] != [
            "toxformat/SKILL.md"
        ]:
            raise ValueError("ZIP 校验失败")
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    skill = members([ROOT / "toxformat", ROOT / "栏目头图与尾图"])
    other = members(
        [
            ROOT / s
            for s in (
                "install.py",
                "README.md",
                "LICENSE",
                "tests",
                "tools",
                ".gitignore",
                ".gitattributes",
            )
        ]
    )
    for label, files in (("ToxFormat", skill), ("ToxFormat-project", sorted(skill + other))):
        target = ROOT / "dist" / f"{label}-{VERSION}.zip"
        print(write_archive(target, files, skill_only=label == "ToxFormat"), target.name)
