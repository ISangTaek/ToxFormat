"""Install the portable skill into one host, with reversible migration of its predecessor."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "toxformat"


def host_dir(host):
    base = Path.home()
    locations = {
        "codex": Path(os.environ.get("CODEX_HOME") or base / ".codex") / "skills",
        "claude": base / ".claude" / "skills",
        "workbuddy": base / ".workbuddy" / "skills",
        "dsh": Path(os.environ.get("DSH_HOME") or base / ".dsh") / "skills",
        "shared": base / ".agents" / "skills",
    }
    return locations[host]


def inventory(folder):
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).digest()
        for path in folder.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def present(path):
    return os.path.lexists(path)


def destination(parent, name):
    path = parent / name
    if path.parent.resolve() != parent or name not in ("toxformat", "gzh-design"):
        raise ValueError("目标超出指定的技能目录。")
    return path


def validate_package(folder):
    skill = folder / "SKILL.md"
    if not skill.is_file() or "name: toxformat\n" not in skill.read_text(encoding="utf-8"):
        raise ValueError("缺少 ToxFormat 技能入口。")
    if [p.relative_to(folder).as_posix() for p in folder.rglob("SKILL.md")] != ["SKILL.md"]:
        raise ValueError("安装包包含额外技能入口。")


def install(skills_dir, migrate=False):
    directory = skills_dir.expanduser().resolve()
    current = destination(directory, "toxformat")
    legacy = destination(directory, "gzh-design")
    validate_package(SOURCE)
    if current.resolve() == SOURCE or directory.is_relative_to(SOURCE):
        raise ValueError("安装目录应在源码目录以外。")
    legacy_active = (legacy / "SKILL.md").is_file()
    if legacy_active and not migrate:
        raise ValueError("此目录已安装 gzh-design。加 --migrate 可将旧入口移至技能目录外并保留备份。")
    if legacy_active and not (
        "name: gzh-design" in (legacy / "SKILL.md").read_text(encoding="utf-8-sig")
    ):
        raise ValueError("gzh-design 目录包含其他技能，已保留原目录。")
    contents = inventory(SOURCE)
    replace = not (current.is_dir() and inventory(current) == contents)
    if not replace and not legacy_active:
        return current, None
    directory.mkdir(exist_ok=True, parents=True)
    backups = directory.parent / "toxformat-backups"
    backups.mkdir(exist_ok=True)
    moved = []
    with tempfile.TemporaryDirectory(dir=directory.parent, prefix=".toxformat-stage-") as stage:
        staged = Path(stage) / "toxformat"
        if replace:
            shutil.copytree(SOURCE, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            if inventory(staged) != contents:
                raise OSError("安装副本校验失败。")
        save = None
        to_move = [
            p for p, needed in ((legacy, legacy_active), (current, replace)) if needed and present(p)
        ]
        if to_move:
            save = Path(tempfile.mkdtemp(dir=backups, prefix="installation-"))
        try:
            for path in to_move:
                backup = save / path.name
                path.rename(backup)
                moved.append((backup, path))
            if replace:
                staged.rename(current)
        except OSError:
            for backup, original in reversed(moved):
                if not present(original):
                    backup.rename(original)
            raise
    return current, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    host = parser.add_mutually_exclusive_group()
    host.add_argument(
        "--host", choices=("codex", "claude", "workbuddy", "dsh", "shared"), default="codex"
    )
    host.add_argument("--skills-dir", type=Path, help="宿主实际使用的技能目录")
    parser.add_argument("--migrate", action="store_true", help="可恢复地迁移同一目录中的 gzh-design")
    args = parser.parse_args()
    try:
        path, backup = install(args.skills_dir or host_dir(args.host), args.migrate)
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + "\n")
    print("已安装　" + str(path))
    if backup:
        print("旧入口备份　" + str(backup))
    print("在宿主重新加载技能或开启新会话后使用。")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
