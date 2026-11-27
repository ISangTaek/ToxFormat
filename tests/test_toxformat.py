"""Exercise the portable CLI from a different working directory using redistributable Word files."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "toxformat/scripts/toxformat.py"
FIXTURES = ROOT / "tests/fixtures"
FILES = [next(FIXTURES.glob(f"*-{code}*.docx")) for code in "ZAM"]
CODES = "ZAM"
TITLES = ["城市树荫温度观测", "图书馆照度记录", "步道客流计数"]
CAPTIONS = ["图1　Z 区温度观测", "图1　A 区照度记录", "图1　M 区客流计数"]


class ArticleHTML(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.fragments = []
        self.image_sources = []
        self.targets = []
        self.feed(body)
        self.text = "".join(self.fragments)

    def handle_data(self, data):
        if data.strip():
            self.fragments.append(data)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "img":
            self.image_sources.append(attributes["src"])
        if tag == "a":
            self.targets.append(attributes["href"])


class WorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="toxformat test ")
        cls.work = Path(cls.temp.name)
        cls.response = cls.command("format", *FILES, "--out", cls.work / "first")
        cls.out = Path(cls.response["output"])
        cls.body = (cls.out / "正文.html").read_text(encoding="utf-8")
        cls.html = ArticleHTML(cls.body)
        cls.manifest = json.loads((cls.out / "复验清单.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def command(cls, *args, expected=0):
        process = subprocess.run(
            [sys.executable, "-X", "utf8", str(CLI), *map(str, args)],
            cwd=cls.work,
            capture_output=True,
            check=False,
            encoding="utf-8",
        )
        if process.returncode != expected:
            raise AssertionError((process.returncode, process.stdout[-800:], process.stderr[-800:]))
        return json.loads(process.stdout)

    def test_each_slot_owns_title_credit_figure_caption_link_qr(self):
        from base64 import b64decode

        blocks = self.manifest["blocks"]
        self.assertEqual([b["text"] for b in blocks if b["role"] == "paper"], TITLES)
        prior = -1
        for slot, (path, title, caption, code, author) in enumerate(
            zip(FILES, TITLES, CAPTIONS, CODES, ("林一", "陈二", "吴三")), 1
        ):
            with zipfile.ZipFile(path) as doc:
                originals = [doc.read(n) for n in doc.namelist() if n.startswith("word/media/")]
            figures = [i["image"] for b in blocks if b["paper"] == slot for i in b["images"]]
            self.assertEqual([hashlib.sha256(x).hexdigest() for x in originals], figures)
            rendered = self.html.image_sources[1 + (slot - 1) * 2 : 1 + slot * 2]
            self.assertEqual(originals, [b64decode(x.split(",", 1)[1]) for x in rendered])
            url = "https://example.org/toxformat-fixtures/" + code
            start = self.html.text.index(title)
            stop = self.html.text.index(url, start)
            self.assertLess(prior, start)
            self.assertIn("作者：" + author, self.html.text[start:stop])
            self.assertIn(caption, self.html.text[start:stop])
            self.assertIn(url, self.html.targets)
            prior = stop
        self.assertEqual(self.html.text.count("转载须知"), 1)
        self.assertEqual(self.html.text.count("扫描二维码"), 3)
        self.assertTrue(self.html.text.endswith("END"))
        self.assertNotIn("本文看点", self.html.text)
        self.assertNotIn("编者按", self.html.text)
        self.assertEqual(self.html.text.count("点击上方"), 0)
        art = ROOT / "栏目头图与尾图"
        self.assertEqual(b64decode(self.html.image_sources[0].split(",")[1]), (art / "论文速读_栏目头图.png").read_bytes())
        self.assertEqual(b64decode(self.html.image_sources[-1].split(",")[1]), (art / "未毒先知_公众号尾图.png").read_bytes())

    def test_repeated_run_and_alias_are_byte_identical(self):
        repeat = self.command(
            "format", *FILES, "--theme", "论文速读-紫罗兰", "--out", self.work / "again"
        )
        again = Path(repeat["output"])
        for name in ("正文.html", "预览.html", "复验清单.json", "审稿参考.md"):
            self.assertEqual((self.out / name).read_bytes(), (again / name).read_bytes())
        same_dir = self.command("format", *FILES, "--out", self.work / "first")
        self.assertEqual(self.out, Path(same_dir["output"]))
        self.assertEqual(self.response["theme"], "文献速读-紫罗兰")
        spans = [
            (b["text"][s["start"] : s["end"]], s["text"])
            for b in self.manifest["blocks"]
            for s in b["added_emphasis"]
        ]
        self.assertNotIn(("置信区间", "置信区间"), spans)
        self.assertEqual(len(spans), 3)
        self.assertTrue(all(a == b for a, b in spans))
        self.assertTrue(
            any(
                b["text"][s["start"] : s["end"]] == "原始读数"
                for b in self.manifest["blocks"]
                for s in b["word_marks"]
                if s["marks"].get("bold")
            )
        )

    def test_explicit_order_routes_one_article(self):
        order = (FILES[2], FILES[0], FILES[1])
        info = self.command("format", *order, "--out", self.work / "reordered")
        self.assertNotEqual(self.response["input_sha256"], info["input_sha256"])
        new = json.loads((Path(info["output"]) / "复验清单.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [b["text"] for b in new["blocks"] if b["role"] == "paper"], [TITLES[2], TITLES[0], TITLES[1]]
        )

    def test_unstyled_heading_before_byline(self):
        plain = self.work / "文献速读-20261121-内部稿号.docx"
        with zipfile.ZipFile(FILES[0]) as src, zipfile.ZipFile(plain, "w") as dest:
            for entry in src.infolist():
                data = src.read(entry)
                if entry.filename == "word/document.xml":
                    data = data.replace(b'<w:pStyle w:val="Title"/>', b"", 1)
                dest.writestr(entry, data)
        batch = self.command("inspect", plain, *FILES[1:])
        self.assertEqual([u["text"] for u in batch["units"] if u["role"] == "paper"], TITLES)

    def test_advisory_findings_do_not_change_copy(self):
        inspect = self.command("inspect", *FILES)
        row = next(u for u in inspect["units"] if "42 次" in u["text"])
        evidence = {
            "input_sha256": inspect["input_sha256"],
            "facts": {
                row["id"]: [
                    {
                        "claim": row["text"],
                        "status": "不一致",
                        "source": "模拟原文-A.md",
                        "locator": "结果 / 表 1 合计",
                        "evidence": "合计为 24 次。",
                    }
                ]
            },
        }
        path = self.work / "evidence.json"
        path.write_text(json.dumps(evidence, ensure_ascii=False), encoding="utf-8")
        output = self.command("format", *FILES, "--out", self.work / "review", "--fact-check", "--evidence", path)
        out = Path(output["output"])
        report = (out / "审稿参考.md").read_text(encoding="utf-8")
        for value in ("建议大修", "数椐", "模拟原文-A.md", "24 次", "待核"):
            self.assertIn(value, report)
        self.assertEqual(self.body, (out / "正文.html").read_text(encoding="utf-8"))
        self.assertIn("42 次", self.html.text)
        self.assertIn("数椐", self.html.text)
        self.assertNotIn("稿前参考报告", self.body)
        swapped = self.command("report", FILES[1], FILES[0], FILES[2], "--fact-check", "--evidence", path)
        self.assertIn("校验值不匹配", swapped["report"])
        self.assertNotIn("模拟原文-A.md", swapped["report"])

    def test_routes_and_proof_modes(self):
        anonymous = self.work / "未命名.docx"
        shutil.copyfile(FILES[0], anonymous)
        self.assertEqual(self.command("inspect", anonymous, expected=2)["status"], "needs_input")
        report = self.command("inspect", anonymous, "--column", "文献解析")
        self.assertEqual(report["theme"], "文献解析-紫罗兰")
        self.assertEqual(self.command("inspect", *FILES[:2], expected=2)["status"], "needs_input")
        self.assertEqual(
            self.command("inspect", FILES[0], FILES[0], FILES[2], expected=2)["status"], "needs_input"
        )
        self.assertEqual(self.command("inspect", FILES[0], "--draft")["theme"], "文献速读-紫罗兰")
        overrides = self.command(
            "format", *FILES, "--theme", "石墨极简风", "--follow", "--note", "编辑明确提供按语。", "--out", self.work
        )
        self.assertEqual((Path(overrides["output"]) / "正文.html").read_text(encoding="utf-8").count("点击上方"), 1)
        self.assertEqual(overrides["theme_id"], "graphite-minimal")
        self.assertIn(
            "编辑明确提供按语。", (Path(overrides["output"]) / "正文.html").read_text(encoding="utf-8")
        )

    def test_all_registered_themes_keep_manuscript(self):
        for theme in self.command("themes")["themes"]:
            with self.subTest(theme=theme):
                data = self.command("format", *FILES, "--theme", theme, "--out", self.work / "themes")
                body = (Path(data["output"]) / "正文.html").read_text(encoding="utf-8")
                html = ArticleHTML(body)
                self.assertTrue(all(title in html.text for title in TITLES))
                self.assertIn("原始读数", html.text)
                self.assertNotIn("{{", body)
                self.assertEqual(len(html.image_sources), 8)

    def test_default_review_and_follow_up(self):
        report = (self.out / "审稿参考.md").read_text(encoding="utf-8")
        self.assertIn("AI 感预警", report)
        self.assertIn("错别字", report)
        self.assertNotIn("原始文献事实核查", report)
        self.assertIn("是否", self.response["follow_up"])
        self.assertIsNone(self.response["audit"]["fact_counts"])
        self.assertEqual(self.command("inspect", *FILES)["fact_ids"], [])
        self.assertTrue(self.command("inspect", *FILES, "--fact-check")["fact_ids"])
        audit = self.command("report", *FILES, "--evidence", ROOT / "tests/模拟合刊核查.json")["audit"]
        self.assertEqual(audit["facts"], [])

    def test_optional_theme_image_handoff(self):
        self.assertIsNone(self.response["theme_image"])
        self.assertIn("合刊", self.response["theme_image_follow_up"])
        enabled = self.command("format", *FILES, "--theme-image", "--out", self.out.parent)
        self.assertEqual(enabled["output"], self.response["output"])
        self.assertIsNone(enabled["theme_image_follow_up"])
        self.assertEqual(enabled["follow_up"], self.response["follow_up"])
        handoff = enabled["theme_image"]
        self.assertTrue(Path(handoff["workflow"]).is_file())
        self.assertEqual(Path(handoff["manuscript"]), self.out / "复验清单.json")
        single = self.command("format", FILES[0], "--column", "文献解析", "--fact-check",
                              "--note", "生成主题图", "--out", self.work / "single")
        self.assertIsNone(single["theme_image"])
        self.assertIn("这篇稿件", single["theme_image_follow_up"])
        self.assertIsNone(single["follow_up"])

    def test_reject_binary_doc(self):
        binary = next((ROOT / "tests/legacy").glob("*.doc"))
        proc = subprocess.run(
            [sys.executable, str(CLI), "format", str(binary), *map(str, FILES[1:])],
            capture_output=True, encoding="utf-8", cwd=self.work,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("另存为 .docx", json.loads(proc.stderr)["message"])
