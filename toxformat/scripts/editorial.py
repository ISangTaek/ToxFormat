"""Reproducible style scoring, proof-reading suggestions and source-bound review records."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from reprint_notice import REMINDER, has_notice
from sections import LABEL, ROOT, urls

RULES = json.loads((ROOT / "assets/editorial-rules.json").read_text(encoding="utf-8"))
PROSE = {"body", "field", "note", "list"}
NONFACT = {"divider", "end", "qr", "image", "scan", "notice", "notice_title", "credit", "source"}
QUOTED = re.compile(r"“[^”]*”|「[^」]*」|『[^』]*』|《[^》]*》|\"[^\"\n]*\"")
PROTECTED = re.compile(
    r"https?://[^\s，。！？；（）<>]+|10\.\d{4,9}/[^\s，。；（）]+|\b(?:Fig|Figs|et al|e\.g|i\.e|vs)\.|\d+\.\d+(?:\.\d+)*",
    re.IGNORECASE,
)


def sentences(text):
    masked = PROTECTED.sub(lambda m: "_" * len(m[0]), text)
    # Preserve symbol positions for comparison back to Word.
    pattern = r"[。！？!?]+[”」』’\"']*|(?<!\d)\.(?=\s+[A-Z]|$)|\n+"
    ends = [m.end() for m in re.finditer(pattern, masked)]
    left = 0
    for right in [*ends, len(text)]:
        raw = text[left:right]
        start = left + len(raw) - len(raw.lstrip())
        sentence = raw.strip()
        if sentence:
            yield start, sentence
        left = right


def units(article):
    result = []
    # Publication metadata is auditable even though it sits outside the paste fragment.
    from manuscript import Block, Run

    aggregate = any(b.paper > 1 for b in article.blocks)
    metadata = [Block("title", [Run(article.title)], role="article_title", paper=0 if aggregate else 1)]
    metadata += [Block("byline", [Run(article.author)], role="credit")] if article.author else []
    references = False
    for b in [*metadata, *article.walk()]:
        if b.role in ("heading", "paper", "subheading"):
            references = b.text.strip().rstrip("：:").casefold() in (
                "参考文献",
                "references",
                "引用文献",
            )
        masked_quotes = QUOTED.sub(lambda m: " " * len(m[0]), b.text)
        in_table = re.search(r"\.r\d+c\d+(?:\.|$)", b.id) is not None
        for i, (start, s) in enumerate(sentences(b.text), 1):
            result.append(
                {
                    "id": f"{b.id}.s{i}",
                    "block": b.id,
                    "paper": b.paper,
                    "role": b.role,
                    "start": start,
                    "text": s,
                    "links": urls(b),
                    "style_text": masked_quotes[start : start + len(s)]
                    if not (in_table or references)
                    else "",
                }
            )
    return result


def plain(sentence):
    s = QUOTED.sub(" ", sentence)
    s = PROTECTED.sub(" ", s)
    return LABEL.sub("", s).strip()


def tags(sentence):
    s = plain(sentence)
    for phrase in RULES["protected_terms"]:
        s = s.replace(phrase, " ")
    opening = next((x for x in RULES["openers"] if s.startswith(x)), "")
    frames = {x for x in RULES["frames"] if re.search(x, s)}
    clues = []
    if any(re.search(rx, s) for rx in RULES["formula_opener"]) or any(
        re.search(rx + r"[。！!？?.,，\s]*$", s) for rx in RULES["formula_ending"]
    ):
        clues.append("套式铺垫或收尾")
    words = [x for x in RULES["promotion"] if x in s]
    if len(words) >= 2:
        clues.append("宣传词汇同句出现（" + "、".join(words) + "）")
    residue = any(re.search(rx, s, re.IGNORECASE) for rx in RULES["residue"])
    return opening, frames, clues, residue


def score_style(items):
    papers = defaultdict(list)
    for item in items:
        if item["paper"] > 0:
            papers.setdefault(item["paper"], [])
        if (
            item["paper"] > 0
            and item["role"] in PROSE
            and re.search(r"[\w\u3400-\u9fff]", plain(item["style_text"]))
        ):
            papers[item["paper"]].append(item)
    scores = []
    for paper, group in sorted(papers.items()):
        hits = []
        previous = []
        for item in group:
            opener, frames, clues, residue = tags(item["style_text"])
            if opener and any(opener == o for o, _ in previous[-2:]):
                clues.append("邻近句首重复（" + opener + "）")
            if any(frames & f for _, f in previous[-2:]):
                clues.append("邻近修辞句式重复")
            previous.append((opener, frames))
            if residue:
                clues.append("明确的对话残留")
            points = 2 if residue else min(2, len(clues))
            if points:
                hits.append({"id": item["id"], "text": item["text"], "points": points, "why": clues})
        denominator = 2 * max(5, len(group))
        total = 100 * sum(h["points"] for h in hits)
        score = (2 * total + denominator) // (2 * denominator)
        scores.append(
            {
                "paper": paper,
                "sentences": len(group),
                "score": score if group else None,
                "advice": "缺少可评叙述正文"
                if not group
                else "建议大修"
                if score >= 50
                else "建议局部调整"
                if score >= 25
                else "模板化表达较少",
                "hits": hits,
            }
        )
    return scores


def load_evidence(path, digest):
    if path is None:
        return {}, []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or data.get("input_sha256") != digest:
            raise ValueError("原稿校验值不匹配")
        if not isinstance(data.get("facts", {}), dict) or not isinstance(data.get("typos", []), list):
            raise TypeError("facts 应为对象，typos 应为数组")
        return data, []
    except (OSError, ValueError, TypeError) as exc:
        return {}, ["外部核查记录未采用，本次按已有材料报告：" + str(exc)]


def proofread(items, evidence):
    findings = []
    for item in items:
        for word, fix in RULES["typos"].items():
            for match in re.finditer(re.escape(word), item["text"]):
                if word == "的的" and item["text"][max(0, match.start() - 1) : match.end()] == "目的的":
                    continue
                findings.append(
                    {
                        "id": item["id"],
                        "word": word,
                        "suggestion": fix,
                        "why": "校对词表命中，请结合上下文核对",
                        "offset": item["start"] + match.start(),
                    }
                )
    lookup = {item["id"]: item["text"] for item in items}
    for row in evidence.get("typos", []):
        if (
            isinstance(row, dict)
            and all(
                isinstance(row.get(k), str) and row[k].strip()
                for k in ("id", "word", "suggestion", "why")
            )
            and row["word"] in lookup.get(row["id"], "")
            and not any(f["id"] == row["id"] and f["word"] == row["word"] for f in findings)
        ):
            findings.append({k: row[k] for k in ("id", "word", "suggestion", "why")})
    papers = {item["id"]: item["paper"] for item in items}
    for finding in findings:
        finding["paper"] = papers[finding["id"]]
    return findings


def fact_candidates(items):
    return [
        u
        for u in items
        if u["role"] not in NONFACT
        and (u["paper"] > 0 or u["role"] == "article_title")
        and not (u["role"] in ("heading", "subheading", "paper", "article_title") and len(u["text"]) < 5)
    ]


def fact_rows(items, evidence):
    result = []
    notes = []
    for item in fact_candidates(items):
        source_rows = evidence.get("facts", {}).get(item["id"], [])
        if not isinstance(source_rows, list):
            source_rows = []
        accepted = []
        for row in source_rows:
            if not isinstance(row, dict) or not all(isinstance(v, str) for v in row.values()):
                continue
            claim = row.get("claim", "")
            status = row.get("status", "")
            if (
                not claim
                or claim not in item["text"]
                or status not in ("一致", "不一致", "待核", "无可核事实")
            ):
                continue
            if status in ("一致", "不一致") and not all(
                row.get(k, "").strip() for k in ("source", "locator", "evidence")
            ):
                continue
            if status in ("待核", "无可核事实") and not row.get("evidence", "").strip():
                continue
            accepted.append(
                {
                    "id": item["id"],
                    "paper": item["paper"],
                    **{k: row.get(k, "") for k in ("claim", "status", "source", "locator", "evidence")},
                }
            )
        result.extend(accepted)
        # An exact extract anchors each finding. Remaining substantive text stays visible.
        remainder = item["text"]
        for row in accepted:
            remainder = remainder.replace(row["claim"], " ", 1)
        if not accepted or re.search(r"[\u3400-\u9fffA-Za-z0-9]{2,}", remainder):
            result.append(
                {
                    "id": item["id"],
                    "paper": item["paper"],
                    "claim": remainder.strip() if accepted else item["text"],
                    "status": "待核",
                    "source": "",
                    "locator": "",
                    "evidence": "此段尚缺可定位的原文证据。",
                }
            )
        if source_rows and len(accepted) < len(source_rows):
            notes.append(item["id"] + " 的部分记录缺少原稿摘录、有效状态或原文证据。")
    return result, notes


def analyze(article, digest, evidence_path=None, fact_check=False):
    items = units(article)
    evidence, notes = load_evidence(evidence_path, digest)
    facts, incomplete = fact_rows(items, evidence) if fact_check else ([], [])
    notice = has_notice(b.text for b in article.blocks)
    scores = score_style(items)
    return {
        "rules": RULES["version"],
        "input_sha256": digest,
        "scores": scores,
        "score": max((p["score"] for p in scores if p["score"] is not None), default=None),
        "typos": proofread(items, evidence),
        "fact_check": fact_check,
        "facts": facts,
        "reprint_notice": notice,
        "notes": article.issues + notes + incomplete + ([] if notice else [REMINDER]),
    }


def report_text(article, audit, theme, sources):
    def esc(s):
        return str(s).replace("|", "｜").replace("\n", " ")

    lines = [
        "# 稿前参考报告",
        "",
        article.title,
        "",
        f"主题为{theme}。以下建议供编辑参考，本次按提交的原稿排版。",
        "",
        "## AI 感预警",
        "",
        f"规则版本 {audit['rules']}。0–24 分提示较少，25–49 分建议局部调整，50–100 分建议大修。",
    ]
    if audit["score"] is not None:
        slots = "、".join(str(g["paper"]) for g in audit["scores"] if g["score"] == audit["score"])
        lines.extend(["", f"最高 {audit['score']}/100 分，位于第 {slots} 篇。"])
    if len(sources) > 1:
        lines.extend(["", *(f"- 第 {s['slot']} 篇　{s['file']}" for s in sources)])
    for g in audit["scores"]:
        value = "未评分" if g["score"] is None else f"{g['score']}/100"
        lines.extend(["", f"第 {g['paper']} 篇　**{value}**　{g['advice']}（{g['sentences']} 句）。"])
        if g["hits"]:
            lines.append("")
        for h in g["hits"]:
            lines.append(f"- {h['id']}　{h['points']} 分　{'、'.join(h['why'])}　{h['text']}")
    if not audit["scores"]:
        lines.append("缺少可评的叙述正文。")
    lines += ["", "## 错别字", ""]
    for row in audit["typos"]:
        position = f"第 {row['paper']} 篇" if row["paper"] else "合刊"
        lines.append(
            f"- {position} / {row['id']}　“{row['word']}”建议核对为“{row['suggestion']}”。{row['why']}"
        )
    if not audit["typos"]:
        lines.append("本次检查未标出疑似错字。")
    if audit["fact_check"]:
        lines += ["", "## 原始文献事实核查", ""]
        counts = {
            k: sum(f["status"] == k for f in audit["facts"])
            for k in ("一致", "不一致", "待核", "无可核事实")
        }
        lines.append("　".join(f"{k} {v} 项" for k, v in counts.items()))
        lines += ["", "| 篇次与位置 | 稿件所述 | 结论 | 原文依据与位置 |", "| --- | --- | --- | --- |"]
        for row in audit["facts"]:
            evidence = " ".join(row[k] for k in ("evidence", "locator", "source") if row[k])
            lines.append(
                "| "
                + " | ".join(
                    map(
                        esc,
                        [f"{row['paper'] or '合刊'} / {row['id']}", row["claim"], row["status"], evidence],
                    )
                )
                + " |"
            )
    if audit["notes"]:
        lines += ["", "## 材料说明", "", *("- " + n for n in audit["notes"])]
    return "\n".join(lines) + "\n"
