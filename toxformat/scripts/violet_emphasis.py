"""Select journal names and a small number of findings across one published article."""

import re

from editorial import sentences
from sections import LABEL


EN_NAME = r"[A-Z][A-Za-z0-9&'’:.\-]*(?:[ \t]+(?:[A-Z][A-Za-z0-9&'’:.\-]*|of|the|and|in|for|on|&))*"
JOURNAL = re.compile(
    r"(?:发表于|发表在|刊登于|刊载于|期刊(?:名称|名)?\s*[:：]|杂志\s*[:：]|在)\s*《(?P<quoted>[^《》\n]+)》"
    r"|《(?P<before>[^《》\n]+)》\s*(?=杂志|期刊|[（(]\s*IF)"
    r"|(?:发表于|发表在|刊登于|刊载于|期刊(?:名称|名)?\s*[:：])\s*(?P<named>" + EN_NAME + r")"
    r"|(?P<publication>" + EN_NAME + r")\s*(?=[（(]\s*IF\b|(?:期刊|杂志)|上发表)"
)


def journal_spans(block):
    spans = {m.span(m.lastgroup) for m in JOURNAL.finditer(block.text)}
    if block.role == "metadata" and not spans:
        name = re.match(r"\s*《?([^《》；;（(，,：:\n]+?)》?\s*(?=[（(]\s*IF)", block.text)
        if name:
            spans.add(name.span(1))
    return sorted(spans)


def article_journals(article):
    blocks = list(article.walk())
    names = {b.text[a:z] for b in blocks for a, z in journal_spans(b)}
    if not names:
        return {}
    pattern = re.compile(
        r"(?<![A-Za-z0-9])(?:"
        + "|".join(re.escape(name) for name in sorted(names, key=lambda n: (-len(n), n)))
        + r")(?![A-Za-z0-9])"
    )
    return {
        b.id: [m.span() for m in pattern.finditer(b.text)]
        for b in blocks if b.role not in ("source", "code", "qr")
    }


def key_sentences(article):
    candidates = []
    section = ""
    for order, block in enumerate(article.blocks):
        if block.role in ("heading", "paper"):
            section = block.text
        if block.role not in ("field", "body", "list") or section.startswith("参考文献"):
            continue
        label = LABEL.match(block.text.lstrip())
        finding = re.search(r"结果|结论|总结|主要发现", label[1] if label else section)
        for start, text in sentences(block.text):
            if label and start == len(block.text) - len(block.text.lstrip()):
                start += label.end()
                text = block.text[start:start + len(text) - label.end()]
            signal = re.search(r"(?:研究|结果|分析|数据)(?:表明|显示|发现)|显著(?:提高|降低|增加|减少)|优于", text)
            if not (finding or signal) or len(text.strip()) < 6 or "http" in text:
                continue
            rank = (0 if signal else 1, 0 if finding else 1, order, start)
            candidates.append((rank, block, start, start + len(text)))
    selected = {}
    papers = set()
    for spread in (True, False):
        for _, block, start, end in sorted(candidates, key=lambda c: c[0]):
            if block.id in selected or (spread and block.paper in papers):
                continue
            selected[block.id] = (start, end)
            papers.add(block.paper)
            if len(selected) == 3:
                return selected
    return selected
