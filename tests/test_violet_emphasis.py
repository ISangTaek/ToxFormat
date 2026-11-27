import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "toxformat/scripts"))
from manuscript import Article, Block, Run
from render_article import Renderer


class VioletTest(unittest.TestCase):
    def test_both_themes_use_the_same_inline_styles_and_issue_budget(self):
        blocks = [
            Block("j", [Run("发表于 Nature "), Run("Communications（IF：18.1）。")]),
            Block("k", [Run("按置信区间报告。")]),
        ]
        blocks.extend(
            Block(str(i), [Run("结果：两组均值分别为 26 和 24。")], role="field", paper=i)
            for i in (1, 1, 2, 3)
        )
        for i, b in enumerate(blocks):
            b.id = str(i)
        for col, theme in (("文献解析", "violet-folio"), ("文献速读", "violet-digest")):
            with self.subTest(theme=theme):
                r = Renderer(Article(blocks, {}, []), col, theme)
                journal = r.inline(blocks[0])
                self.assertEqual(journal.count("color:#000000;font-style:italic;"), 2)
                self.assertIn("</strong><span leaf=\"\">（IF：18.1）", journal)
                self.assertIn('font-weight:700;color:#000000;"><span leaf="">置信区间', r.inline(blocks[1]))
                marked = [b.paper for b in blocks if "color:#5D4679" in r.inline(b)]
                self.assertEqual(marked, [1, 2, 3])
