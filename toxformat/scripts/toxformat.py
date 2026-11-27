#!/usr/bin/env python3
"""ToxFormat portable entry point. Run with Python 3.9 or newer."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

from editorial import RULES, analyze, fact_candidates, report_text, units
from manuscript import Block, Run, sha
from render_article import Renderer
from sections import CATALOG, ROOT, SelectionError
from submission import load_submission
from validate_gzh_html import validate

MEDIA_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/tiff": "tif",
    "image/svg+xml": "svg",
}


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def write_text(path, text):
    path.write_bytes(text.encode("utf-8"))


def slug(name):
    safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")[:58]
    return safe or "稿件"


def entry_manifest(b, renderer):
    spans = [{"start": a, "end": z, "text": b.text[a:z]} for a, z in renderer.spans[b.id]]
    originals = []
    images = []
    links = []
    offset = 0
    for r in b.runs:
        if r.image:
            images.append({"at": offset, "image": r.image})
        if r.marks and r.text:
            originals.append({"start": offset, "end": offset + len(r.text), "marks": dict(r.marks)})
        if r.link:
            links.append({"at": offset, "href": r.link, "text": r.text})
        offset += len(r.text)
    return {
        "id": b.id,
        "paper": b.paper,
        "role": b.role,
        "text": b.text,
        "images": images,
        "links": links,
        "word_marks": originals,
        "added_emphasis": spans,
    }


def preview_page(body, renderer):
    article = renderer.article
    theme = renderer.theme
    h = html.escape
    if theme["layout"] == "digest":
        template = (ROOT / "assets/digest-preview-template.html").read_text(encoding="utf-8")
        downloads = []
        for pos, r in enumerate(article.cover, 1):
            mime = article.media.get(r.image, ("",))[0]
            downloads.append(
                f'<a href="{h(renderer.data_url(r.image))}" download="封面-{pos}.{MEDIA_EXT.get(mime, "bin")}">封面 {pos}</a>'
            )
        picture_index = 0
        for b in article.walk():
            for r in b.runs:
                if r.image:
                    name = ("原文二维码" if b.role == "qr" else "图片") + str(picture_index + 1)
                    if b.paper:
                        name = f"第{b.paper}篇-{name}"
                    mime = article.media.get(r.image, ("",))[0]
                    downloads.append(
                        f'<a data-i="{picture_index + renderer.header_images}" href="#" download="{name}.{MEDIA_EXT.get(mime, "bin")}">{name}</a>'
                    )
                    picture_index += 1
        values = {
            "TITLE": h(article.title),
            "THEME": h(theme["name"]),
            "BODY": body,
            "BYLINE": h(article.author) + "　" if article.author else "",
            "ACCOUNT": h(CATALOG["account"]),
            "FILENAME": h(slug(article.title) + ".html"),
            "FRONT_COUNT": str(renderer.front_count),
            "HAS_NOTE": "yes" if article.blocks and article.blocks[0].role == "note" else "no",
            "DOWNLOADS": "<h3>稿件素材</h3><nav>" + "".join(downloads) + "</nav>" if downloads else "",
        }
        return re.sub(r"\{\{([A-Z_]+)}}", lambda m: values[m[1]], template)
    template = (ROOT / "assets/preview-template.html").read_text(encoding="utf-8")
    meta = (
        '<header style="margin:0 auto 18px;max-width:677px;padding:14px;background:white;box-sizing:border-box;"><small>'
        + h(theme["name"])
        + '</small><h1 style="font-size:22px;line-height:1.45;margin:6px 0;">'
        + h(article.title)
        + "</h1>"
    )
    if article.author:
        meta += '<p style="font-size:13px;margin:5px 0;">' + h(article.author) + "</p>"
    meta += "</header>"
    return (
        template.replace("#059669", theme["ink"])
        .replace("#047857", theme["title"])
        .replace("{{TITLE}}", h(article.title) + " · " + h(theme["name"]))
        .replace('<div id="gzh-content">', meta + '\n<div id="gzh-content">')
        .replace("<!--GZH_CONTENT-->", body)
    )


def publish(directory, stem, files):
    directory.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    for name, data in sorted(files.items()):
        h.update(name.encode())
        h.update(hashlib.sha256(data).digest())
    target = directory / (slug(stem) + "-" + h.hexdigest()[:12])
    with tempfile.TemporaryDirectory(dir=directory, prefix=".toxformat-") as tmp:
        staged = Path(tmp) / "article"
        staged.mkdir()
        for name, data in files.items():
            (staged / name).write_bytes(data)
        try:
            staged.rename(target)
        except OSError:
            if not target.is_dir() or not all(
                (target / n).is_file() and (target / n).read_bytes() == d for n, d in files.items()
            ):
                raise
    return target


def image_mapping(path):
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(url, str) and url.startswith("https://")
        for k, url in data.items()
    ):
        raise ValueError("图片映射需要由图片标识和 HTTPS 素材地址组成。")
    return data


def execute(args):
    if args.command == "themes":
        return {
            "columns": CATALOG["columns"],
            "themes": {
                i: {"name": t["name"], "aliases": t["aliases"], "version": t["version"]}
                for i, t in CATALOG["themes"].items()
            },
        }
    article, col, theme_id, digest, inputs = load_submission(
        args.files, args.column, args.theme, args.title, args.mode
    )
    if args.note:
        article.blocks.insert(
            0, Block("editor-note", [Run("编者按：" + args.note)], role="note", paper=0)
        )
    theme = CATALOG["themes"][theme_id]
    info = {
        "input_sha256": digest,
        "sources": inputs,
        "column": col,
        "theme": theme["name"],
        "theme_id": theme_id,
        "theme_version": theme["version"],
        "package_version": CATALOG["version"],
        "rules_version": RULES["version"],
        "title": article.title,
        "byline": article.author,
        "converter": article.converter,
    }
    if args.command == "inspect":
        items = units(article)
        facts = fact_candidates(items) if args.fact_check else []
        media_files = {}
        if args.media_dir:
            folder = Path(args.media_dir).resolve()
            folder.mkdir(parents=True, exist_ok=True)
            for key, (mime, data) in article.media.items():
                path = folder / f"{key}.{MEDIA_EXT.get(mime, 'bin')}"
                path.write_bytes(data)
                media_files[key] = str(path)
        return {
            **info,
            "units": items,
            "fact_ids": [u["id"] for u in facts],
            "notes": article.issues,
            "template_notes": article.template_notes,
            "media": list(article.media),
            "media_files": media_files,
            "media_by_block": [
                {
                    "paper": b.paper,
                    "block": b.id,
                    "role": b.role,
                    "image": r.image,
                    "alt": r.alt,
                    "link": r.link,
                }
                for b in article.walk()
                for r in b.runs
                if r.image
            ],
        }
    audit = analyze(article, digest, args.evidence, fact_check=args.fact_check)
    report = report_text(article, audit, theme["name"], inputs)
    if args.command == "report":
        if args.save:
            write_text(Path(args.save), report)
        return {**info, "report": report, "audit": audit}
    if args.command != "format":
        raise ValueError("无法识别命令")
    mapping = image_mapping(args.image_map)
    renderer = Renderer(article, col, theme_id, mapping)
    body = renderer.render(follow=args.follow)
    errors, warnings, leaf_count = validate(body)
    if errors:
        raise ValueError("公众号 HTML 校验错误：" + "、".join(errors))
    preview = preview_page(body, renderer)
    manifest = {
        **info,
        "body_sha256": sha(body.encode()),
        "blocks": [entry_manifest(b, renderer) for b in article.walk()],
        "cover_media": [r.image for r in article.cover],
        "audit_summary": {
            "score": audit["score"],
            "typos": len(audit["typos"]),
            "fact_check": args.fact_check,
            "fact_counts": {
                s: sum(f["status"] == s for f in audit["facts"])
                for s in ("一致", "不一致", "待核", "无可核事实")
            } if args.fact_check else None,
        },
        "html_validation": {"errors": errors, "warnings": warnings, "leaf_spans": leaf_count},
    }
    files = {
        "正文.html": body.encode(),
        "预览.html": preview.encode(),
        "审稿参考.md": report.encode(),
        "复验清单.json": json_text(manifest).encode(),
    }
    for i, r in enumerate(article.cover, 1):
        if r.image in article.media:
            mime, data = article.media[r.image]
            files[f"封面-{i}.{MEDIA_EXT.get(mime, 'bin')}"] = data
    label = (
        (Path(args.files[0]).stem if len(inputs) == 1 else f"{col}-{len(inputs)}篇合刊")
        + "_"
        + theme["name"]
    )
    target = publish(Path(args.out).resolve(), label, files)
    return {
        **info,
        "output": str(target),
        "report": str(target / "审稿参考.md"),
        "preview": str(target / "预览.html"),
        "follow_up": None if args.fact_check else "是否要对照原始文献进行事实核查？",
        "body_sha256": manifest["body_sha256"],
        "audit": manifest["audit_summary"],
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("themes")
    for name in ("inspect", "report", "format"):
        cmd = commands.add_parser(name)
        cmd.add_argument("files", nargs="+", help="一个稿件，或按篇位顺序提供多份速读 Word")
        cmd.add_argument("--column")
        cmd.add_argument("--theme")
        cmd.add_argument("--title", help="微信标题或合刊标题")
        cmd.add_argument("--note", help="编辑明确指定的按语")
        cmd.add_argument("--fact-check", action="store_true", help="编辑明确要求时启用原始文献事实核查")
        modes = cmd.add_mutually_exclusive_group()
        modes.add_argument(
            "--draft", dest="mode", action="store_const", const="draft", help="试排一至多篇速读"
        )
        modes.add_argument(
            "--legacy-combined",
            dest="mode",
            action="store_const",
            const="legacy",
            help="试排一份已合并的旧版速读样稿",
        )
        cmd.set_defaults(mode="issue")
        if name in ("report", "format"):
            cmd.add_argument("--evidence", help="依据原稿和原论文核查后的 JSON 记录")
        if name == "report":
            cmd.add_argument("--save", help="另存 Markdown 参考报告")
        if name == "inspect":
            cmd.add_argument("--media-dir", help="按图片校验值提取 Word 中的原图和二维码")
            cmd.add_argument("--save", help="将完整 JSON 保存到文件")
        if name == "format":
            cmd.add_argument("--follow", action="store_true", help="按编辑要求加入刊首关注提示")
            cmd.add_argument("--out", default="ToxFormat输出")
            cmd.add_argument("--image-map", help="可选的图片 SHA-256 到已上传素材 HTTPS 地址的 JSON")
    args = parser.parse_args()
    try:
        result = execute(args)
        if args.command == "inspect" and args.save:
            write_text(Path(args.save), json_text(result))
            result = {
                "inspection": str(Path(args.save).resolve()),
                "input_sha256": result["input_sha256"],
                "column": result["column"],
                "units": len(result["units"]),
            }
    except SelectionError as exc:
        print(json_text({"status": "needs_input", "question": str(exc)}))
        return 2
    except (OSError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        print(json_text({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json_text(result), end="")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
