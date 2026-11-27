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
            Block("k", [Run("按置信区间报告。", (("bold", True), ("color", "5D4679")))]),
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
                self.assertNotIn("<strong", r.inline(blocks[1]))
                marked = [b.paper for b in blocks if "color:#5D4679" in r.inline(b)]
                self.assertEqual(marked, [1, 2, 3])


    def test_opening_overview_and_main_result(self):
        from violet_emphasis import key_sentences
        blocks = [
            Block("background", [Run("既往研究表明，此类物质与多种疾病相关。")]),
            Block("lead", [Run("本研究识别出高风险类别，并揭示其共同特征。")]),
            Block("methods", [Run("研究方法")], role="heading"),
            Block("sample", [Run("研究团队收集了300个样本。")]),
            Block("results", [Run("研究结果")], role="heading"),
            Block("main", [Run("独立验证中，新模型的预测精度显著高于基线。")]),
            Block("end", [Run("结论")], role="heading"),
            Block("recap", [Run("本研究表明新模型可以提高预测精度。")]),
        ]
        self.assertEqual(set(key_sentences(Article(blocks, {}, []))), {"lead", "main"})

    def test_reprint_notice_must_contain_terms_at_the_end(self):
        from reprint_notice import has_notice
        policy = "未经授权禁止转载。"
        self.assertTrue(has_notice(["正文。", policy, "编辑：小张", "END"]))
        self.assertFalse(has_notice([policy, "下面介绍本研究。", "转载声明", "END"]))
        self.assertFalse(has_notice(["正文。", "转载声明", "END"]))
