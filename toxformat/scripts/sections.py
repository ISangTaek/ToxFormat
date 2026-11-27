"""Column routing and publication metadata. All decisions use registered names or source structure."""

from __future__ import annotations

import json
import re
from pathlib import Path

from manuscript import Article, Block, Run, safe_link, sha

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "assets/catalog.json").read_text(encoding="utf-8"))
DIVIDER = re.compile(r"^(?:[—─━_\-=＊*·•]\s*){3,}$")
AUTHOR = re.compile(r"^(?:推文)?(?:作者|撰稿|编辑|审核|校对|排版|责编)[：:]")
LABEL = re.compile(
    r"^(研究背景|研究方法|研究结果|研究结论|背景|目的|方法|结果|结论|意义|局限|要点)[：:]"
)
NOTE = re.compile(r"^(?:【(编者按[语]?|按语|编者的话)】[：:]?|(编者按[语]?|按语|编者的话)[：:])\s*")
CAPTION = re.compile(r"^(?:图\s*[A-Za-z]?\d+|表\s*\d+|Fig(?:ure)?\.?\s*\d+)", re.IGNORECASE)
SOURCE = re.compile(r"^(?:原文(?:链接|网址)?|论文(?:链接|网址)|DOI)\s*[：:]", re.IGNORECASE)
URL = re.compile(r"https?://[^\s<>「」《》【】（）“”。，；！？、]+", re.IGNORECASE)
META = re.compile(
    r"(?:[（(]\s*IF\s*[：:=]|\b(?:19|20)\d{2}[-./年]\d{1,2}[-./月]\d{1,2}.{0,70}(?:团队|组|实验室))",
    re.IGNORECASE,
)
SCAN = re.compile(r"(?:扫(?:描)?(?:该|上方|下方)?二维码|扫码).{0,12}(?:阅读|原文|查看)")
CHAPTERS = {
    "研究方法概览": "METHODS",
    "研究结果概览": "RESULTS",
    "研究背景": "BACKGROUND",
    "研究方法": "METHODS",
    "研究结果": "RESULTS",
    "讨论": "DISCUSSION",
    "结论": "CONCLUSION",
    "引言": "INTRODUCTION",
    "总结": "SUMMARY",
    "参考文献": "REFERENCES",
}


class SelectionError(ValueError):
    pass


def resolve_column(stem, explicit=None):
    cols = CATALOG["columns"]
    if explicit:
        matches = [name for name, c in cols.items() if explicit == name or explicit in c["prefixes"]]
    else:
        head = re.split(r"[\s\-—–_｜|：:]+", stem.strip(), maxsplit=1)[0]
        matches = [name for name, c in cols.items() if head in c["prefixes"]]
    if len(matches) != 1:
        raise SelectionError("这份稿件属于" + "还是".join(cols) + "？用 --column 提供编辑的选择。")
    return matches[0]


def resolve_theme(column, explicit=None):
    if not explicit or explicit in ("紫罗兰", "紫罗兰配色"):
        return CATALOG["columns"][column]["default"]
    for key, t in CATALOG["themes"].items():
        if explicit in [key, t["name"], *t["aliases"]]:
            return key
    raise SelectionError("主题库中没有这个名称：" + explicit + "。可选主题用 themes 查看。")


def split_front(article, stem):
    bs = article.blocks
    # The house submission template encloses its publication title/byline in two rules.
    rules = [i for i, b in enumerate(bs[:18]) if DIVIDER.fullmatch(b.text.strip())]
    if len(rules) >= 2:
        left, right = rules[:2]
        before = bs[:left]
        head = bs[left + 1 : right]
        if (
            (not before or all(re.match(r"^注\s*\d+[：:]", b.text.strip()) for b in before))
            and head
            and any(AUTHOR.match(b.text.strip()) for b in head)
        ):
            article.template_notes = [b.text for b in before]
            article.title = head[0].text.strip()
            article.title_block = head[0]
            article.author_blocks = [b for b in head[1:] if AUTHOR.match(b.text.strip())]
            article.author = "　".join(b.text for b in head[1:] if AUTHOR.match(b.text.strip()))
            # Preserve extra content of nonstandard publication headers.
            bs = [b for b in head[1:] if not AUTHOR.match(b.text.strip())] + bs[right + 1 :]
    if not article.title and bs:
        first = bs[0]
        # Many submitted manuscripts use a plain first line immediately
        # followed by an explicit byline, without a Word title style.
        byline_follows = len(bs) > 1 and AUTHOR.match(bs[1].text.strip())
        plain_title = (
            byline_follows
            and first.role == "body"
            and not first.has_image
            and 0 < len(first.text.strip()) <= 160
            and not NOTE.match(first.text.strip())
            and not LABEL.match(first.text.strip())
            and not first.text.strip().endswith("。")
        )
        if (
            first.style.lower() in ("title", "标题", "文档标题")
            or first.role == "title"
            or first.text.startswith(("推文标题：", "标题：", "推文标题:", "标题:"))
            or plain_title
        ):
            article.title = re.sub(r"^(推文标题|标题)[：:]", "", first.text).strip()
            article.title_block = first if article.title == first.text.strip() else None
            bs = bs[1:]
            if bs and AUTHOR.match(bs[0].text.strip()):
                article.author = bs[0].text.strip()
                article.author_blocks = [bs[0]]
                bs = bs[1:]
    if not article.title:
        article.title = re.sub(r"^[^-]+-\d{8}-", "", stem)
    for i, b in enumerate(bs):
        if b.text.strip() not in ("封面图片：", "封面图片:", "封面图：", "封面图:"):
            continue
        tail = bs[i + 1 :]
        if tail and all(x.has_image and not x.text.strip() for x in tail):
            article.cover = [r for x in tail for r in x.runs if r.image]
            bs = bs[:i]
            if bs and DIVIDER.fullmatch(bs[-1].text.strip()):
                bs = bs[:-1]
            break
    article.blocks = bs


def classify(article, column, stem):
    split_front(article, stem)
    bs = article.blocks
    digest = CATALOG["columns"][column]["structure"] == "digest"
    paper = 0
    footer = False
    for i, b in enumerate(bs):
        t = b.text.strip()
        following = bs[i + 1].text.strip() if i + 1 < len(bs) else ""
        prev = bs[i - 1] if i else None
        if b.role not in ("body", "heading", "subheading"):
            pass
        elif t in ("转载须知", "转载声明", "版权声明"):
            footer = True
            b.role = "notice_title"
        elif footer and t.startswith(("【原创", "未经", "本文为", "本公众号")):
            b.role = "notice"
        elif NOTE.match(t):
            b.role = "note"
        elif b.style.casefold() in ("quote", "intense quote", "引用", "明显引用"):
            b.role = "quote"
        elif t == "END":
            b.role = "end"
        elif DIVIDER.fullmatch(t):
            b.role = "divider"
        elif b.has_image and SCAN.search(t) and len(t) < 36:
            b.role = "qr"
        elif SCAN.search(t) and len(t) < 36:
            b.role = "scan"
        elif b.has_image and not t:
            b.role = (
                "qr"
                if (
                    SCAN.search(following)
                    or prev
                    and prev.role in ("source", "scan")
                    and not CAPTION.match(following)
                )
                else "image"
            )
        elif AUTHOR.match(t):
            b.role = "credit"
        elif SOURCE.match(t) or URL.fullmatch(t.rstrip("。.）")) or t.startswith("点击“阅读原文”"):
            b.role = "source"
        elif CAPTION.match(t):
            b.role = "caption"
        elif LABEL.match(t):
            b.role = "field" if digest else "body"
        elif digest and META.search(t):
            b.role = "metadata"
        elif (
            digest
            and not footer
            and t
            and (
                META.search(following)
                or b.level in (1, 2)
                or (b.align == "center" and len(t) < 65 and not re.search(r"[！？。]$", t))
            )
        ):
            paper += 1
            b.role = "paper"
        elif (
            t in CHAPTERS
            or b.level in (1, 2)
            or (b.align == "center" and t and len(t) < 35 and not footer and not b.has_image)
        ):
            b.role = "heading"
        elif b.level >= 3 or (
            len(t) < 70
            and t
            and all(dict(r.marks).get("bold") for r in b.runs if r.text.strip())
            and not re.search(r"[。！？；]$", t)
        ):
            b.role = "subheading"
        elif b.bullet:
            b.role = "list"
        b.paper = (paper or 1) if not footer else 0

        def tag_cells(parent):
            for row in parent.rows:
                for cell in row:
                    for child in cell:
                        child.paper = parent.paper
                        tag_cells(child)

        tag_cells(b)
    return article


def urls(block):
    result = []
    for run in block.runs:
        if run.link and safe_link(run.link):
            result.append(run.link)
    result.extend(m.group().rstrip(".,);]") for m in URL.finditer(block.text))
    return list(dict.fromkeys(result))


def read_markup(source):
    """Basic exchange format for the upstream normalization workflow."""
    import mimetypes

    text = source.read_text(encoding="utf-8-sig")
    article = Article([], {}, [])
    inline = re.compile(
        r"!\[([^\]]*)\]\(([^)]+)\)|\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|==(.+?)==|\+\+(.+?)\+\+|<u>(.+?)</u>|~~(.+?)~~|\x60([^\x60]+)\x60"
    )

    def inlines(line):
        runs = []
        start = 0
        for m in inline.finditer(line):
            if m.start() > start:
                runs.append(Run(line[start : m.start()]))
            if m[2]:
                url = m[2]
                if safe_link(url):
                    runs.append(Run(alt=m[1], image=url))
                else:
                    path = (source.parent / url).resolve()
                    if path.is_file():
                        data = path.read_bytes()
                        key = sha(data)
                        article.media[key] = (
                            mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                            data,
                        )
                        runs.append(Run(alt=m[1], image=key))
                    else:
                        runs.append(Run(line[m.start() : m.end()]))
                        article.issues.append("找不到图片：" + url)
            elif m[4]:
                runs.append(Run(m[3], link=safe_link(m[4])))
            else:
                tag = next(k for k in range(5, 11) if m[k] is not None)
                name = {
                    5: "bold",
                    6: "highlight",
                    7: "underline",
                    8: "underline",
                    9: "strike",
                    10: "code",
                }[tag]
                runs.append(Run(m[tag], ((name, "yellow" if tag == 6 else True),)))
            start = m.end()
        if start < len(line):
            runs.append(Run(line[start:]))
        return runs

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        start = i + 1
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if line.startswith(chr(96) * 3):
            code = []
            while i < len(lines) and not lines[i].lstrip().startswith(chr(96) * 3):
                code.append(lines[i])
                i += 1
            i += 1
            article.blocks.append(Block(f"p{start}", [Run("\n".join(code))], role="code"))
            continue
        if "|" in line and i < len(lines) and re.fullmatch(r"[\s|:\-]+", lines[i]) and "-" in lines[i]:
            tab = [line]
            i += 1
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                tab.append(lines[i])
                i += 1
            rows = [
                [
                    [Block(f"p{start}.r{n}c{c}", inlines(v.strip()))]
                    for c, v in enumerate(row.strip().strip("|").split("|"), 1)
                ]
                for n, row in enumerate(tab, 1)
            ]
            article.blocks.append(Block(f"p{start}", role="table", rows=rows))
            continue
        role = "body"
        h = re.match(r"^(#{1,6})\s+(.*)", line)
        level = 0
        bullet = ""
        if h:
            level = len(h[1])
            line = h[2]
            role = "title" if level == 1 and not article.blocks else "heading"
        elif line.startswith(">"):
            role = "quote"
            line = line.lstrip(">").strip()
        else:
            item = re.match(r"^([-*+]|\d+[.)])\s+(.*)", line)
            if item:
                role = "list"
                bullet = item[1]
                line = item[2]
        article.blocks.append(Block(f"p{start}", inlines(line), level=level, role=role, bullet=bullet))
    return article
