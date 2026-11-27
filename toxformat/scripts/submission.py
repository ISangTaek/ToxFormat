"""Bind every paper, source asset and review location to the editor's input order."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from publication_art import last_body_image, search_card
from manuscript import Article, Block, Run, read_word
from sections import (
    CATALOG,
    CHAPTERS,
    SelectionError,
    classify,
    read_markup,
    resolve_column,
    resolve_theme,
)


def read_one(path, column):
    if path.suffix.lower() == ".docx":
        raw = read_word(path)
        index = last_body_image((b.text, b.has_image) for b in raw.blocks)
        if index is not None:
            block = raw.blocks[index]
            block.runs = [r for r in block.runs if not search_card(r.image)]
            if not block.runs and not block.rows:
                raw.blocks.pop(index)
    elif path.suffix.lower() in {".md", ".markdown", ".txt"}:
        raw = read_markup(path)
    else:
        raise ValueError("请先按 references/format-normalize.md 将 PDF 或网页正文归一化为 Markdown。")
    return classify(raw, column, path.stem)


def footer_key(block):
    # Deduplicate intact copyright text and identical account artwork only in the
    # explicitly labelled footer. Source QR codes are always local to their paper.
    return block.role, tuple((r.text, r.image, r.link, r.marks) for r in block.runs)


def merge_digest(articles, title):
    combined = Article([], {}, [])
    shared_footer = []
    seen = set()
    repeated_art = {}
    for article in articles:
        for key in {
            r.image
            for b in article.blocks
            if b.paper == 0 and b.role in ("image", "credit")
            for r in b.runs
            if r.image
        }:
            repeated_art[key] = repeated_art.get(key, 0) + 1

    headings = []
    for slot, article in enumerate(articles, 1):
        prefix = f"d{slot}."
        combined.media.update(article.media)
        combined.issues.extend(f"第 {slot} 篇　{issue}" for issue in article.issues)
        combined.cover.extend(article.cover)
        combined.template_notes.extend(article.template_notes)
        for block in article.walk():
            block.id = prefix + block.id
            if block.paper:
                block.paper = slot

        first = article.blocks[0] if article.blocks else None
        # A Word title followed by an internal heading uses the Word title.
        # The submission template can instead provide a platform headline and
        # a distinct, centered paper heading immediately above the journal line.
        own_heading = (
            first
            and first.role == "paper"
            and first.text.strip() not in CHAPTERS
            and (
                not article.title_block
                or len(article.blocks) > 1
                and article.blocks[1].role == "metadata"
                or first.text.strip() == article.title
            )
        )
        if own_heading:
            heading = first
        elif article.title_block:
            heading = article.title_block
            heading.id = prefix + heading.id
        else:
            heading = Block(prefix + "title", [Run(article.title)])
        heading.role, heading.paper = "paper", slot
        headings.append(heading.text.strip())
        combined.blocks.append(heading)

        credits = {b.text.strip() for b in article.blocks if b.role == "credit"}
        for b in article.author_blocks:
            if b.text.strip() not in credits:
                b.id, b.role, b.paper = prefix + b.id, "credit", slot
                combined.blocks.append(b)
        for b in article.blocks:
            if b is heading or b.role == "end":
                continue
            if b.paper == 0 and b.role in ("notice", "notice_title"):
                key = footer_key(b)
                if key not in seen:
                    shared_footer.append(b)
                    seen.add(key)
                continue
            if b.paper == 0 and b.role in ("image", "credit"):
                local = []
                for index, run in enumerate(b.runs):
                    if run.image and repeated_art.get(run.image, 0) > 1:
                        key = ("account-card", run.image)
                        if key not in seen:
                            shared_footer.append(
                                Block(f"{b.id}.card{index}", [run], role="image", paper=0)
                            )
                            seen.add(key)
                    else:
                        local.append(run)
                b.runs = local
                if not b.text.strip() and not b.has_image:
                    continue
            if b.role == "paper":
                b.role = "subheading"
            b.paper = slot
            combined.blocks.append(b)

    combined.blocks.extend(shared_footer)
    combined.title = title or f"文献速读｜{headings[0]}等{len(articles)}篇"
    combined.converter = ", ".join(dict.fromkeys(a.converter for a in articles if a.converter))
    return combined


def load_submission(
    paths, selected_column=None, selected_theme=None, title=None, mode="issue"
):
    files = [Path(p).resolve() for p in paths]
    if not files:
        raise ValueError("请选择稿件。")
    if any(path.suffix.lower() == ".doc" for path in files):
        raise ValueError("请将旧版 .doc 稿件另存为 .docx 后提交。")
    columns = [resolve_column(path.stem, selected_column) for path in files]
    column = columns[0]
    digest_column = CATALOG["columns"][column]["structure"] == "digest"
    if len(set(columns)) != 1 or (len(files) > 1 and not digest_column):
        raise SelectionError("合刊需要同一速读栏目的稿件。请确认各文件所属栏目。")
    if digest_column and mode == "issue" and len(files) != 3:
        raise SelectionError(
            f"文献速读正式合刊需要三份独立 Word，当前收到 {len(files)} 份。请补齐或指定三个篇位；单篇试排可使用 --draft，已有合刊旧样可使用 --legacy-combined。"
        )
    if mode == "legacy" and (len(files) != 1 or not digest_column):
        raise SelectionError("旧版合刊模式适用于一份内含多篇的文献速读稿。")
    if (
        digest_column
        and mode == "issue"
        and any(p.suffix.lower() != ".docx" for p in files)
    ):
        raise SelectionError(
            "文献速读正式合刊需要三个篇位对应的原始 Word。其他格式可使用 --draft 预览。"
        )

    theme = resolve_theme(column, selected_theme)
    inputs = []
    docs = []
    hashes = set()
    for slot, path in enumerate(files, 1):
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        if checksum in hashes:
            raise SelectionError("重复提交了同一份稿件。请按篇位提供内容不同的文件。")
        hashes.add(checksum)
        doc = read_one(path, column)
        inputs.append(
            {
                "slot": slot,
                "file": path.name,
                "sha256": checksum,
                "title": doc.title,
                "byline": doc.author,
                "cover_media": [r.image for r in doc.cover],
            }
        )
        docs.append(doc)

    if digest_column and mode != "legacy":
        article = merge_digest(docs, title)
        if len(docs) == 1:
            article.title = title or docs[0].title
    else:
        article = docs[0]
    if title:
        article.title = title
    if len(inputs) == 1:
        digest = inputs[0]["sha256"]
    else:
        # Ordered input identity is portable across host paths and attachment renames.
        digest = hashlib.sha256(
            json.dumps([s["sha256"] for s in inputs], separators=(",", ":")).encode()
        ).hexdigest()
    return article, column, theme, digest, inputs
