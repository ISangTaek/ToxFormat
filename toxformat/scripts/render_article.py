"""Render the registered component libraries without asking a model to assemble HTML."""

from __future__ import annotations

import base64
import html
import re
from urllib.parse import unquote

from sections import CATALOG, CHAPTERS, LABEL, NOTE, ROOT, URL
from violet_emphasis import article_journals, key_sentences


def esc(s):
    return html.escape(str(s), quote=True)


def leaf(s):
    return '<span leaf="">' + esc(s).replace("\n", "<br>") + "</span>"


def template_parts(path):
    text = path.read_text(encoding="utf-8")
    parts = {}
    for heading, body in re.findall(r"^#{2,3} (.+?)\n([\s\S]*?)(?=^#{2,3} |\Z)", text, re.MULTILINE):
        fence = re.search(r"\x60{3}html\n([\s\S]*?)\x60{3}", body)
        if fence:
            fragment = re.sub(r"<!--[\s\S]*?-->", "", fence[1]).strip()
            parts[heading] = re.sub(r"\{\{([^}]+)}}", lambda m: "{{" + unquote(m[1]) + "}}", fragment)
    return parts


def fill(fragment, values):
    """Values are escaped HTML or escaped attribute text; preserve styles found in the component."""
    pattern = r'<span leaf="">\{\{([^{}]+)}}</span>|\{\{([^{}]+)}}'

    def replace(m):
        key = m[1] or m[2]
        if key not in values:
            return ""
        content = values[key]
        return content if not m[1] or "<" in content else '<span leaf="">' + content + "</span>"

    return re.sub(pattern, replace, fragment)


def select_spans(block, column):
    text = block.text
    fixed = []
    offset = 0
    for run in block.runs:
        end = offset + len(run.text)
        marks = dict(run.marks)
        protected = bool(
            run.link
            or any(
                marks.get(k)
                for k in ("bold", "italic", "underline", "strike", "highlight", "vertAlign", "code")
            )
            or re.fullmatch(r"(?!000000|FFFFFF)[0-9A-F]{6}", marks.get("color", "").upper())
        )
        if protected and end > offset:
            fixed.append((offset, end))
        offset = end
    protected = fixed + [(m.start(), m.end()) for m in URL.finditer(text)]
    if block.role not in ("body", "field", "list") or column["max_emphasis"] <= 0:
        return []
    candidates = []
    for term in column["terms"]:
        candidates.extend(
            (0, m.start(), -len(term), m.end(), term) for m in re.finditer(re.escape(term), text)
        )
    exprs = [
        r"(?<![A-Za-z0-9_.])\d+(?:\.\d+)?\s*(?:[%％]|个百分点|例|种物种|个终点)",
        r"(?:\b[A-Z][A-Za-z0-9-]{2,}\b|(?<![A-Za-z])[A-Z][A-Za-z0-9-]*[A-Z][A-Za-z0-9-]+)(?![A-Za-z])",
    ]
    for rank, expr in enumerate(exprs, 1):
        candidates.extend((rank, m.start(), -len(m[0]), m.end(), m[0]) for m in re.finditer(expr, text))
    selected = []
    used = set()
    for _, start, _, end, word in sorted(candidates):
        if word in used or any(start < b and a < end for a, b in protected + selected):
            continue
        selected.append((start, end))
        used.add(word)
        if len(selected) >= column["max_emphasis"]:
            break
    return sorted(selected)


class Renderer:
    def __init__(self, article, column, theme_id, image_map=None, sentence_emphasis="source"):
        self.article = article
        self.column = CATALOG["columns"][column]
        self.theme = CATALOG["themes"][theme_id]
        self.parts = template_parts(ROOT / self.theme["component_file"])
        self.family = self.theme["layout"]
        self.ink = self.theme["ink"]
        self.line = self.theme["line"]
        self.dark = self.theme["title"]
        self.paper = self.theme["paper"]
        self.violet = theme_id in ("violet-folio", "violet-digest")
        self.spans = {b.id: [] if self.violet else select_spans(b, self.column) for b in article.walk()}
        self.special = {}
        if self.violet:
            findings = key_sentences(article, sentence_emphasis)
            journals = article_journals(article)
            for block in article.walk():
                spans = [(a, z, "journal") for a, z in journals.get(block.id, ())]
                spans.extend((a, z, "finding") for a, z in findings.get(block.id, ()))
                self.special[block.id] = spans
        self.images = {}
        self.image_map = image_map or {}
        self.heading_no = 0
        self.paper_count = sum(b.role == "paper" for b in article.blocks)

    def part(self, phrase):
        return next((v for k, v in self.parts.items() if phrase in k), "")

    def data_url(self, key):
        if key in self.image_map:
            return self.image_map[key]
        if key not in self.article.media:
            return key if key.startswith(("https://", "http://")) else ""
        if key not in self.images:
            mime, data = self.article.media[key]
            self.images[key] = "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")
        return self.images[key]

    def image(self, run, inline=False, qr=False):
        style = (
            ("width:84px;" if qr else "")
            + "max-width:100%;height:auto;"
            + (
                "display:inline-block;vertical-align:middle;"
                if inline
                else "display:block;margin:0 auto;"
            )
        )
        return f'<span leaf=""><img src="{esc(self.data_url(run.image))}" alt="{esc(run.alt)}" style="{style}"></span>'

    def inline(self, b, begin=0, finish=None):
        end_text = len(b.text) if finish is None else finish
        offset = 0
        pieces = []
        auto = self.spans[b.id]
        auto_underline = self.theme.get(
            "underline", f"border-bottom:1px solid {self.ink};font-weight:600;"
        )
        for run in b.runs:
            if run.image:
                if begin <= offset < end_text or finish is None and offset == end_text:
                    picture = self.image(run, inline=bool(b.text.strip()), qr=b.role == "qr")
                    if run.link:
                        picture = f'<a href="{esc(run.link)}">{picture}</a>'
                    pieces.append(picture)
                continue
            left = offset
            offset += len(run.text)
            lo, hi = max(left, begin), min(offset, end_text)
            if lo >= hi:
                continue
            marks = dict(run.marks)
            ranges = [(max(lo, a), min(hi, z), "em") for a, z in auto if a < hi and z > lo]
            for a, z, kind in self.special.get(b.id, ()):
                if a < hi and z > lo:
                    ranges.append((max(lo, a), min(hi, z), kind))
            for m in URL.finditer(b.text):
                url = m.group().rstrip(".,);]")
                a, z = m.start(), m.start() + len(url)
                if a < hi and z > lo and not run.link:
                    ranges.append((max(a, lo), min(z, hi), url))
            bounds = sorted({lo, hi, *(a for a, z, k in ranges), *(z for a, z, k in ranges)})
            for a, z in zip(bounds, bounds[1:]):
                raw = run.text[a - left : z - left]
                value = leaf(raw)
                css = []
                if not self.violet and any(x <= a < y and t == "em" for x, y, t in ranges):
                    css.append(auto_underline)
                active = {t for x, y, t in ranges if x <= a < y}
                if self.violet and active & {"finding", "journal"}:
                    color = self.ink if "finding" in active and "journal" not in active else "#000000"
                    italic = "font-style:italic;" if "journal" in active else ""
                    value = f'<strong style="font-weight:700;color:{color};{italic}">{value}</strong>'
                elif not self.violet and marks.get("bold"):
                    value = f'<strong style="font-weight:700;color:{self.dark};">{value}</strong>'
                if marks.get("italic"):
                    css.append("font-style:italic;")
                deco = " ".join(
                    name
                    for key, name in (("underline", "underline"), ("strike", "line-through"))
                    if marks.get(key)
                )
                if deco:
                    css.append("text-decoration:" + deco + ";")
                color = marks.get("color", "")
                if not self.violet and re.fullmatch("[0-9a-fA-F]{6}", color) and color.lower() not in {"000000", "ffffff"}:
                    css.append("color:#" + color + ";")
                hilite = marks.get("highlight", "")
                if re.fullmatch("[a-zA-Z]+", hilite) and hilite not in ("none", "auto"):
                    css.append("background-color:" + hilite + ";")
                align = marks.get("vertAlign")
                if align in ("superscript", "subscript"):
                    css.append(
                        "vertical-align:"
                        + ("super" if align == "superscript" else "sub")
                        + ";font-size:0.8em;"
                    )
                if marks.get("code"):
                    css.append("font-family:Consolas,monospace;")
                if css:
                    value = '<span style="' + "".join(css) + '">' + value + "</span>"
                href = run.link or next((t for x, y, t in ranges if x <= a < y and t not in {"em", "finding", "journal"}), "")
                if href:
                    value = f'<a href="{esc(href)}" style="color:{self.ink};text-decoration:underline;overflow-wrap:anywhere;">{value}</a>'
                pieces.append(value)
        return "".join(pieces)

    def divider(self):
        part = self.part("章节分割线") or self.part("篇间分隔")
        if part and "gradient" not in part:
            return part
        return f'<section style="border-top:1px solid {self.line};margin:22px 0;height:0;"><span leaf=""><br></span></section>'

    def para(self, content):
        tpl = self.part("正文段落")
        if tpl and "{{" in tpl:
            return fill(tpl, {"正文段落": content, "正文内容": content})
        style = re.search(r'<p style="([^"]+)"', tpl)
        css = (
            style[1]
            if style
            else f"font-size:15px;line-height:1.9;margin:0 0 15px;color:{self.dark};overflow-wrap:break-word;"
        )
        return f'<p style="{css}">{content}</p>'

    def heading(self, b):
        content = self.inline(b)
        self.heading_no += 1
        label = CHAPTERS.get(b.text.strip(), "")
        num = f"{self.heading_no:02d}"
        if b.role == "paper" and self.family == "digest":
            tpl = self.part("篇序与论文标题")
            if self.paper_count <= 1:
                tpl = tpl.replace("{{篇序}} / {{篇数}}", "{{篇序}}")
            return fill(
                tpl,
                {
                    "篇序": str(b.paper).zfill(2),
                    "篇数": str(self.paper_count).zfill(2),
                    "论文短标题": content,
                },
            )
        if self.family == "folio":
            return fill(self.part("一级章题"), {"英文章签": esc(label or num), "章节标题": content})
        tpl = self.part("章节标题")
        if tpl and "{{" in tpl:
            tpl = tpl.replace(">01</span>", f">{num}</span>")
            values = {k: content for k in ("中文标题", "中文章节标题", "标题")}
            values.update({k: esc(label) for k in ("ENGLISH TAG", "ENGLISH · 英文副标题", "副标题")})
            values.update({"编号": num, "01": num})
            return fill(tpl, values)
        return f'<h3 style="color:{self.dark};font:600 21px/1.6 Georgia,serif;margin:28px 0 14px;border-bottom:1px solid {self.line};">{content}</h3>'

    def subhead(self, b):
        content = self.inline(b)
        tpl = self.part("左竖线小标题") or self.part("小节标题") or self.part("子标题")
        if tpl and "{{" in tpl:
            return fill(tpl, {"小节标题": content, "子标题": content})
        return f'<h4 style="border-left:3px solid {self.ink};padding-left:10px;color:{self.dark};font-size:16px;margin:22px 0 12px;">{content}</h4>'

    def caption(self, b):
        return f'<p style="text-align:center;font-size:12px;line-height:1.65;margin:7px 0 17px;color:{self.ink};">{self.inline(b)}</p>'

    def display(self, b):
        if b.role in ("heading", "paper"):
            return self.heading(b)
        if b.role == "subheading":
            return self.subhead(b)
        if b.role == "divider":
            return self.divider()
        if b.role == "end":
            return ""
        if b.role == "image" or b.role == "qr":
            return '<section style="margin:18px 0 9px;">' + self.inline(b) + "</section>"
        if b.role in ("scan", "caption", "credit"):
            return self.caption(b)
        if b.role == "list":
            return self.para(leaf((b.bullet or "•") + "　") + self.inline(b))
        if b.role == "source":
            return f'<p style="font-size:13px;line-height:1.7;overflow-wrap:anywhere;margin:10px 0;">{self.inline(b)}</p>'
        if b.role == "metadata":
            sep = re.search(r"[；;]", b.text)
            cut = sep.end() if sep else len(b.text)
            bottom = self.inline(b, cut)
            return (
                f'<section style="border-left:2px solid {self.line};padding:5px 0 5px 11px;margin:0 0 16px;"><p style="font:600 15px/1.6 Georgia,serif;color:{self.dark};margin:0;">{self.inline(b, 0, cut)}</p>'
                + (
                    f'<p style="font-size:12px;line-height:1.65;color:{self.ink};margin:3px 0;">{bottom}</p>'
                    if bottom
                    else ""
                )
                + "</section>"
            )
        if b.role == "field":
            m = LABEL.match(b.text.lstrip())
            if m:
                cut = len(b.text) - len(b.text.lstrip()) + m.end()
                if self.violet:
                    return self.para(self.inline(b))
                return self.para(
                    f'<strong style="color:{self.ink};">{self.inline(b, 0, cut)}</strong>'
                    + self.inline(b, cut)
                )
        if b.role in ("note", "quote", "notice", "notice_title"):
            if b.role == "note":
                m = NOTE.match(b.text.lstrip())
                cut = len(b.text) - len(b.text.lstrip()) + m.end() if m else 0
                tpl = self.part("编者按")
                if tpl:
                    return fill(tpl, {"按语原文": self.inline(b, cut)})
            return f'<section style="border-left:2px solid {self.ink};background:{self.paper};padding:10px 14px;font-size:14px;line-height:1.8;">{self.inline(b)}</section>'
        if b.role == "code":
            return (
                '<section style="padding:12px;background:#f4f4f4;font-family:Consolas,monospace;">'
                + "".join(
                    '<p style="margin:0;">' + leaf(line.replace(" ", "\u00a0")) + "</p>"
                    for line in b.text.split("\n")
                )
                + "</section>"
            )
        if b.role == "table":
            rows = []
            for row in b.rows:
                cells = [
                    '<td style="border:1px solid '
                    + self.line
                    + ';padding:5px;vertical-align:top;">'
                    + "".join(self.display(c) for c in cell)
                    + "</td>"
                    for cell in row
                ]
                rows.append("<tr>" + "".join(cells) + "</tr>")
            return (
                '<table style="border-collapse:collapse;width:100%;margin:12px 0;">'
                + "".join(rows)
                + "</table>"
            )
        return self.para(self.inline(b))

    def render(self, follow=False):
        from publication_art import FOLLOW, artwork

        header, footer = artwork(self.column['prefixes'][0], self.image_map)
        bs = self.article.blocks
        if header and bs and bs[0].role == "divider":
            bs = bs[1:]
        pieces = [header] if header else []
        if follow:
            invitation = self.part("刊首关注") or FOLLOW
            pieces.append(fill(invitation, {"公众号名称": esc(CATALOG["account"])}))
        self.front_count = len(pieces)
        self.header_images = int(bool(header))
        i = 0
        while i < len(bs):
            block = bs[i]
            i += 1
            if (
                block.role in ("heading", "paper", "notice_title")
                and i > 1
                and bs[i - 2].role != "divider"
            ):
                pieces.append(self.divider())
            if (
                block.role == "source"
                and i < len(bs)
                and bs[i].role == "qr"
                and bs[i].paper == block.paper
            ):
                qr = bs[i]
                i += 1
                caption = ""
                if i < len(bs) and bs[i].role == "scan" and bs[i].paper == block.paper:
                    caption = self.caption(bs[i])
                    i += 1
                pieces.append(
                    f'<section style="display:flex;align-items:center;background:{self.paper};border-top:1px solid {self.line};padding:10px 12px;"><section style="flex:1;min-width:0;padding-right:10px;">{self.display(block)}</section><section style="width:91px;text-align:center;">{self.inline(qr)}{caption}</section></section>'
                )
            else:
                pieces.append(self.display(block))
        end = self.parts.get("END") or self.part("END 收尾")
        if end and "{{" not in end:
            pieces.append(end)
        else:
            pieces.append(
                self.divider()
                + f'<p style="text-align:center;font:13px Georgia,serif;letter-spacing:3px;color:{self.ink};">{leaf("END")}</p>'
            )
        pieces.append(footer)
        container = self.part("全局容器") or self.part("完整文章模板骨架")
        match = re.search(r"<section\b[^>]*>", container)
        start = (
            match[0]
            if match
            else f'<section style="max-width:677px;margin:auto;background:#fff;color:{self.dark};">'
        )
        return start + "\n" + "\n".join(pieces) + "\n</section>"
