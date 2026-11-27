import sys
import tempfile
import unittest
from importlib.util import find_spec
from itertools import groupby
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "toxformat/scripts"))


@unittest.skipUnless(find_spec("PIL"), "主题图排字使用 Pillow")
class DigestMastheadTest(unittest.TestCase):
    def test_row_retains_order_duplicates_aspect_ratios_and_gaps(self):
        from PIL import Image, ImageColor
        from typeset_art import INK, draw_digest_mastheads

        blue, red, paper = (0, 40, 95), (170, 30, 50), (255, 255, 255)
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for index, (length, color) in enumerate(((150, blue), (50, red))):
                logo = Image.new("RGBA", (length + 20, 30))
                logo.paste((*color, 255), (10, 5, 10 + length, 25))
                path = Path(tmp) / f"{index}.png"
                logo.save(path)
                paths.append(path)
            canvas = Image.new("RGB", (1000, 500), paper)
            left, top, width = 40, 25, 650
            height = draw_digest_mastheads(canvas, [paths[0], paths[1], paths[0]], left, top, width)
            pixels = (canvas.getpixel((x, top + height // 2)) for x in range(canvas.width))
            runs = [(color, len(list(group))) for color, group in groupby(pixels)]
            bar = ImageColor.getrgb(INK)
            self.assertEqual([color for color, _ in runs],
                             [paper, blue, paper, bar, paper, red, paper, bar, paper, blue, paper])
            sizes = [count for _, count in runs]
            self.assertEqual(sizes[0], left)
            self.assertLessEqual(sum(sizes[1:-1]), width)
            self.assertEqual(sizes[1], sizes[9])
            self.assertAlmostEqual(sizes[1] / height, 7.5, delta=1 / height)
            self.assertAlmostEqual(sizes[5] / height, 2.5, delta=1 / height)
            self.assertEqual(len({sizes[i] for i in (2, 4, 6, 8)}), 1)
