"""Read WordprocessingML in document order, with text offsets independent of Word runs."""

from __future__ import annotations

import hashlib
import mimetypes
import posixpath
import re
import zipfile
from dataclasses import dataclass, field
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from extract_docx import A, R, W, load_styles

V = "{urn:schemas-microsoft-com:vml}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


@dataclass
class Run:
    text: str = ""
    marks: tuple = ()
    link: str = ""
    image: str = ""
    alt: str = ""


@dataclass
class Block:
    id: str
    runs: list = field(default_factory=list)
    level: int = 0
    style: str = ""
    align: str = ""
    role: str = "body"
    paper: int = 1
    rows: list = field(default_factory=list)
    bullet: str = ""

    @property
    def text(self):
        return "".join(run.text for run in self.runs)

    @property
    def has_image(self):
        return any(run.image for run in self.runs)


@dataclass
class Article:
    blocks: list
    media: dict
    issues: list
    title: str = ""
    author: str = ""
    cover: list = field(default_factory=list)
    template_notes: list = field(default_factory=list)
    converter: str = ""
    title_block: Block | None = None
    author_blocks: list = field(default_factory=list)

    def walk(self):
        def descendants(block):
            yield block
            for row in block.rows:
                for cell in row:
                    for child in cell:
                        yield from descendants(child)

        for block in self.blocks:
            yield from descendants(block)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def value(node, tag, default=""):
    child = node.find(W + tag) if node is not None else None
    return child.get(W + "val", default) if child is not None else default


def mark_values(props):
    marks = {}
    if props is None:
        return marks
    for tag, key in [("b", "bold"), ("i", "italic"), ("strike", "strike"), ("u", "underline")]:
        child = props.find(W + tag)
        if child is not None:
            marks[key] = child.get(W + "val", "1").lower() not in {"false", "0", "none", "off"}
    for tag in ("color", "highlight", "vertAlign"):
        if value(props, tag):
            marks[tag] = value(props, tag)
    return marks


def safe_link(url):
    return url if re.match(r"^(?:https?://|mailto:|#)", url, re.IGNORECASE) else ""


def read_word(source):
    with zipfile.ZipFile(source) as archive:
        return WordReader(archive).read()


class WordReader:
    def __init__(self, archive):
        self.archive = archive
        self.article = Article([], {}, [])
        self.levels = load_styles(archive)
        self.styles = {}
        self.style_cache = {}
        self.default_marks = {}
        self.media_parts = {}
        self.rels = {}
        self.types = {}
        self.overrides = {}
        self.numbers = {}
        self.counters = {}
        self.part = "word/document.xml"
        self.read_metadata()

    def optional_xml(self, name):
        try:
            return ET.fromstring(self.archive.read(name))
        except KeyError:
            return None

    def read_metadata(self):
        root = self.optional_xml("[Content_Types].xml")
        if root is not None:
            for el in root:
                if el.get("Extension"):
                    self.types[el.get("Extension").lower()] = el.get("ContentType", "")
                if el.get("PartName"):
                    self.overrides[el.get("PartName").lstrip("/")] = el.get("ContentType", "")
        root = self.optional_xml("word/_rels/document.xml.rels")
        if root is not None:
            for el in root:
                target = el.get("Target", "")
                external = el.get("TargetMode") == "External"
                part = posixpath.normpath(posixpath.join("word", unquote(target))).lstrip("/")
                self.rels[el.get("Id")] = (target if external else part, external)
        root = self.optional_xml("word/styles.xml")
        if root is not None:
            self.default_marks = mark_values(root.find(f"{W}docDefaults/{W}rPrDefault/{W}rPr"))
            for st in root.findall(W + "style"):
                self.styles[st.get(W + "styleId")] = st
        numbering = self.optional_xml("word/numbering.xml")
        if numbering is not None:
            abstracts = {a.get(W + "abstractNumId"): a for a in numbering.findall(W + "abstractNum")}
            for num in numbering.findall(W + "num"):
                base = abstracts.get(value(num, "abstractNumId"))
                if base is not None:
                    for lvl in base.findall(W + "lvl"):
                        key = num.get(W + "numId"), lvl.get(W + "ilvl", "0")
                        self.numbers[key] = (
                            value(lvl, "numFmt"),
                            value(lvl, "start", "1"),
                            value(lvl, "lvlText", "%1."),
                        )

    def style_props(self, sid, seen=()):
        if not sid or sid in seen or sid not in self.styles:
            return {}
        if sid not in self.style_cache:
            node = self.styles[sid]
            data = dict(self.style_props(value(node, "basedOn"), seen + (sid,)))
            data.update(mark_values(node.find(W + "rPr")))
            self.style_cache[sid] = data
        return self.style_cache[sid]

    def media(self, rid, alt):
        target, external = self.rels.get(rid, ("", False))
        if not target:
            self.article.issues.append("图片关系缺失：" + str(rid))
            return Run(text=alt or "〔原稿图片缺失〕")
        if external:
            if safe_link(target).startswith(("http://", "https://")):
                return Run(image=target, alt=alt)
            self.article.issues.append("外链图片未嵌入：" + target)
            return Run(text=alt or "〔原稿外链图片〕")
        if target not in self.media_parts:
            try:
                data = self.archive.read(target)
            except KeyError:
                self.article.issues.append("原稿图片部件缺失：" + target)
                return Run(text=alt or "〔原稿图片缺失〕")
            key = sha(data)
            ext = target.rsplit(".", 1)[-1].lower()
            mime = (
                self.overrides.get(target)
                or self.types.get(ext)
                or mimetypes.guess_type(target)[0]
                or "application/octet-stream"
            )
            self.article.media[key] = (mime, data)
            self.media_parts[target] = key
        return Run(image=self.media_parts[target], alt=alt)

    def paragraph(self, node, ident):
        props = node.find(W + "pPr")
        sid = value(props, "pStyle")
        st = self.styles.get(sid)
        outline = value(props, "outlineLvl")
        level = int(outline) + 1 if outline.isdigit() and int(outline) < 9 else self.levels.get(sid, 0)
        block = Block(ident, level=level, style=value(st, "name", sid), align=value(props, "jc"))
        num = props.find(W + "numPr") if props is not None else None
        if num is not None:
            key = value(num, "numId"), value(num, "ilvl", "0")
            fmt, start, pattern = self.numbers.get(key, ("bullet", "1", "•"))
            if fmt == "bullet":
                block.bullet = "•"
            elif key[0] != "0":
                self.counters[key] = self.counters.get(key, int(start) - 1) + 1
                block.bullet = re.sub(
                    r"%(\d+)", lambda m: str(self.counters.get((key[0], str(int(m[1]) - 1)), 1)), pattern
                )
        inherited = dict(self.default_marks)
        inherited.update(self.style_props(sid))
        field_link = ""

        def visit(el, props, link=""):
            nonlocal field_link
            tag = el.tag
            if tag in (W + "del", W + "moveFrom", W + "pPr", W + "rPr"):
                return
            if tag == MC + "AlternateContent":
                choice = el.find(MC + "Choice")
                if choice is None:
                    choice = el.find(MC + "Fallback")
                if choice is not None:
                    visit(choice, props, link)
                return
            if tag == W + "r":
                rp = el.find(W + "rPr")
                props = dict(props)
                props.update(self.style_props(value(rp, "rStyle")))
                props.update(mark_values(rp))
            elif tag == W + "hyperlink":
                target = self.rels.get(el.get(R + "id"), ("", False))[0]
                anchor = el.get(W + "anchor", "")
                link = safe_link(target or ("#" + anchor if anchor else ""))
            elif tag in (W + "instrText", W + "fldSimple"):
                instruction = el.text or "" if tag == W + "instrText" else el.get(W + "instr", "")
                m = re.search(r'HYPERLINK\s+"([^"]+)"', instruction, re.IGNORECASE)
                if m:
                    if tag == W + "fldSimple":
                        link = safe_link(m[1])
                    else:
                        field_link = safe_link(m[1])
                if tag == W + "instrText":
                    return
            elif tag == W + "fldChar" and el.get(W + "fldCharType") == "end":
                field_link = ""
            elif tag in (W + "drawing", W + "pict"):
                alt = next(
                    (
                        n.get("descr") or n.get("title")
                        for n in el.iter()
                        if n.get("descr") or n.get("title")
                    ),
                    "",
                )
                for n in el.iter():
                    if n.tag in (A + "blip", V + "imagedata"):
                        rid = n.get(R + "embed") or n.get(R + "link") or n.get(R + "id")
                        if rid:
                            image_run = self.media(rid, alt)
                            image_run.link = link or field_link
                            block.runs.append(image_run)
                    elif n.tag == W + "txbxContent":
                        for sub in n.findall(W + "p"):
                            visit(sub, props, link)
                            block.runs.append(Run(text="\n"))
                return
            elif tag in (
                W + "t",
                M + "t",
                W + "tab",
                W + "br",
                W + "cr",
                W + "noBreakHyphen",
                W + "softHyphen",
            ):
                text = {
                    W + "tab": "\t",
                    W + "br": "\n",
                    W + "cr": "\n",
                    W + "noBreakHyphen": "‑",
                    W + "softHyphen": "\u00ad",
                }.get(tag, el.text or "")
                marks = tuple(sorted((k, v) for k, v in props.items() if v))
                block.runs.append(Run(text=text, marks=marks, link=link or field_link))
                return
            for child in el:
                visit(child, props, link)

        visit(node, inherited)
        return block

    def blocks(self, parent, prefix=""):
        for n, el in enumerate(parent, 1):
            ident = prefix + "p" + str(n)
            if el.tag == W + "p":
                block = self.paragraph(el, ident)
                if block.text.strip() or block.has_image:
                    yield block
            elif el.tag == W + "tbl":
                rows = []
                for i, row in enumerate(el.findall(W + "tr"), 1):
                    cells = [
                        list(self.blocks(c, f"{ident}.r{i}c{j}."))
                        for j, c in enumerate(row.findall(W + "tc"), 1)
                    ]
                    rows.append(cells)
                yield Block(ident, role="table", rows=rows)
            elif el.tag in (W + "sdt", W + "sdtContent", W + "customXml", W + "ins", W + "moveTo"):
                yield from self.blocks(el, ident + ".")

    def read(self):
        document = ET.fromstring(self.archive.read(self.part))
        body = document.find(W + "body")
        if body is None:
            raise ValueError("Word 缺少正文。")
        self.article.blocks = list(self.blocks(body))
        return self.article
