"""Shared publication header, optional follow invitation, and final account artwork."""

import base64
import hashlib
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = "栏目头图与尾图"
FOOTER = "未毒先知_公众号尾图.png"
ALIASES = {"文献解析": "论文解析", "文献速读": "论文速读"}
OLD_SEARCH_CARD = "ff525ca6250bc0750ae5264e646185ef01690c9f14da863759d26c961eb422cf"
FOLLOW = '<p style="text-align:center;margin:6px 0 18px;color:#52525B;font-size:13px;"><span leaf="">↑ 点击上方「未毒先知」关注我们</span></p>'


def artwork(column="", mapping=None):
    directory = ROOT / DIRECTORY
    if not directory.is_dir():
        directory = ROOT.parent / DIRECTORY
    def image(filename):
        data = (directory / filename).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        src = (mapping or {}).get(digest) or "data:image/png;base64," + base64.b64encode(data).decode()
        return ('<section style="margin:12px 0;"><span leaf=""><img style="display:block;width:100%;'
                'height:auto;" alt="' + html.escape(filename[:-4]) + '" src="' + html.escape(src)
                + '"></span></section>')

    prefix = re.split(r"[\s\-—–_｜|：:]+", column.strip(), maxsplit=1)[0]
    name = ALIASES.get(prefix, prefix)
    headers = {p.name[:-len("_栏目头图.png")]: p.name for p in directory.glob("*_栏目头图.png")}
    if name in ("论文解析", "论文速读", "政策法规追踪", "行业动态解读", "科普文化传播") and name not in headers:
        raise ValueError(f"缺少栏目头图：{name}_栏目头图.png")
    return image(headers[name]) if name in headers else "", image(FOOTER)


def last_body_image(rows):
    """Locate the final illustrated paragraph before any separately supplied cover."""
    last = None
    for index, (text, has_image) in enumerate(rows):
        if text.strip() in ("封面图片：", "封面图片:", "封面图：", "封面图:"):
            break
        if has_image:
            last = index
    return last


def search_card(digest):
    # Original Word artwork and the editor's supplied PNG rendition.
    return digest in {OLD_SEARCH_CARD, "ede9c67f7d55a0af9ff10388ac0f03c60b622238f5bdb1d22da496a411a1c1e3"}
