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


OUTCOME = re.compile(r"揭示|识别出|定位出|证实|发现|表明|显示|优于|高于|低于|显著|降低|提高|改善|高度一致|实现了|预测出|排名|伴随")
STUDY = re.compile(r"本研究|该研究|本项研究|研究团队|研究者|该模型|该方法|本工作|这项研究|研究发现|研究表明|研究显示")
RESULT_SECTION = re.compile(r"结果|发现|主要贡献")
DETAIL = re.compile(r"例如|举例|以.{1,15}为例|未来|有望|旨在|此前|既往研究|前人研究")


def source_bold_sentences(article):
    """Use only whole sentences marked bold by the author, in publication order."""
    selected = {}
    count = 0
    for block in article.blocks:
        if block.role not in ("body", "field", "list", "note"):
            continue
        # Word can split a single sentence into runs for fonts, links and revisions.
        bold = [bool(dict(run.marks).get("bold")) for run in block.runs for _ in run.text]
        label = LABEL.match(block.text.lstrip())
        for start, sentence in sentences(block.text):
            end = start + len(sentence)
            if label and start == len(block.text) - len(block.text.lstrip()):
                start += label.end()
            words = [i for i in range(start, end) if block.text[i].isalnum()]
            if not words or not all(bold[i] for i in words):
                continue
            if not re.search(r"""[。！？.!?][”」』’"']*$""", sentence):
                continue
            selected.setdefault(block.id, []).append((start, end))
            count += 1
            if count == 3:
                return selected
    return selected


def key_sentences(article, mode="source"):
    if mode == "source":
        return source_bold_sentences(article)
    if mode == "none":
        return {}
    if mode != "auto":
        raise ValueError("未知的关键句模式：" + mode)
    leads, results = [], []
    section = ""
    opening = True
    paragraphs = 0
    papers = {b.paper for b in article.blocks if b.paper > 0}
    for order, block in enumerate(article.blocks):
        if block.role == "paper":
            section, paragraphs, opening = "", 0, True
        elif block.role in ("heading", "subheading"):
            if block.role == "heading" or RESULT_SECTION.search(block.text):
                section = block.text
            if not re.search(r"引言|导语|背景|摘要|概览", block.text) or re.search(r"方法|结果", block.text):
                opening = False
        if block.role not in ("field", "body", "note", "list") or not block.paper and block.role != "note":
            continue
        stripped = block.text.lstrip()
        label = LABEL.match(stripped)
        context = label[1] if label else section
        result_section = bool(RESULT_SECTION.search(context))
        if label and re.search(r"方法|结果|结论", context):
            opening = False
        if re.search(r"方法|参考文献|展望", context) or (label and not result_section and not opening):
            continue
        paragraphs += 1
        for start, text in sentences(block.text):
            if label and start == len(block.text) - len(stripped):
                start += label.end()
                text = text[label.end():]
            if not 6 <= len(text) <= 240 or "http" in text or DETAIL.search(text) or text.endswith(("?", "？")):
                continue
            span = (block.id, start, start + len(text), block.paper)
            outcome = OUTCOME.search(text)
            if opening and paragraphs <= 3 and not result_section:
                if STUDY.search(text) and outcome and not re.search(r"发表了.{0,6}论文|发表于", text):
                    breadth = bool(re.search(r"同时|并|整体|首次|不仅|从而|为.{1,20}提供", text))
                    leads.append(((not breadth, order, start), span))
            measured = bool(re.search(r"\d", text))
            if not outcome and not (result_section and measured):
                continue
            if not result_section and not (outcome and (STUDY.search(text) or re.search(r"结果表明|结果显示|验证中|验证结果", text))):
                continue
            if re.search(r"进行了|用于|为测试|为验证|为评估", text) and not outcome:
                continue
            rank = (not result_section, not bool(outcome), not measured, order, start)
            results.append((rank, span))
    chosen = []
    lead_position = (-1, -1)
    if leads:
        lead_rank, lead_span = min(leads)
        chosen.append(lead_span)
        lead_position = lead_rank[-2:]
    ranked = [span for rank, span in sorted(results) if rank[-2:] > lead_position]
    # Cover distinct papers first, then distinct paragraphs within the same paper.
    limit = 3 if len(papers) >= 3 else 2
    for distinct in ("paper", "block", "sentence"):
        for span in ranked:
            if len(chosen) >= limit:
                break
            if span in chosen or (distinct == "paper" and any(c[3] == span[3] for c in chosen)):
                continue
            if distinct == "block" and any(c[0] == span[0] for c in chosen):
                continue
            chosen.append(span)
    selected = {}
    for block_id, start, end, _ in chosen:
        selected.setdefault(block_id, []).append((start, end))
    return selected
