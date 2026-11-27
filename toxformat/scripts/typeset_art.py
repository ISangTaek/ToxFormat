"""Typeset a ToxFormat article title on a generated plate using a supplied font."""

import argparse
from itertools import groupby
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INK = "#282A2C"
VIOLET = "#3C1E73"


def fit_text(path, lines, available, largest, smallest):
    for size in range(max(1, largest), max(1, smallest) - 1, -1):
        font = ImageFont.truetype(str(path), size)
        boxes = [font.getbbox(line, anchor="ls") for line in lines]
        if all(right - left <= available for left, _, right, _ in boxes):
            return font, boxes
    raise ValueError("文字超出排字区，请精简或换行。")


def draw_highlight(draw, x, baseline, line, font):
    prefix = ""
    for is_digit, chars in groupby(line, str.isdigit):
        run = "".join(chars)
        # Account for kerning between the preceding text and this color run.
        offset = font.getlength(prefix + run[0]) - font.getlength(run[0])
        draw.text((x + offset, baseline), run, font=font, fill=VIOLET if is_digit else INK,
                  anchor="ls")
        prefix += run


def read_masthead(path):
    with Image.open(path) as asset:
        mark = asset.convert("RGBA")
    bounds = mark.getchannel("A").getbbox()
    if not bounds:
        raise ValueError(f"刊头素材为空：{path}")
    return mark.crop(bounds)


def draw_digest_mastheads(canvas, paths, left, top, available):
    if len(paths) != 3:
        raise ValueError("速读合刊需要按篇位提供三个官方刊头。")
    marks = [read_masthead(path) for path in paths]
    gap = max(1, round(canvas.width * 0.012))
    bar = max(1, round(canvas.width * 0.0015))
    space_for_marks = available - 2 * (2 * gap + bar)
    ratios = [mark.width / mark.height for mark in marks]
    height = int(min(canvas.height * 0.19, space_for_marks / sum(ratios)))
    if height < 1:
        raise ValueError("三个刊头超出排字区，请增加 --width 或调整画幅。")
    draw = ImageDraw.Draw(canvas)
    x = left
    for position, (mark, ratio) in enumerate(zip(marks, ratios)):
        if position:
            x += gap
            draw.rectangle((x, top, x + bar - 1, top + height - 1), fill=INK)
            x += bar + gap
        resized = mark.resize((max(1, int(height * ratio)), height), Image.Resampling.LANCZOS)
        canvas.paste(resized, (x, top), resized)
        x += resized.width
    return height


def typeset(plate, output, font_path, lines, width, accent=None, masthead=None, highlights=(),
            description=None, text_font=None, description_font=None, digest_mastheads=None):
    if not 0 < width <= 0.92 or not 1 <= len(lines) <= 3 or any(not s.strip() for s in lines):
        raise ValueError("请提供一至三行非空标题，排字区宽度须大于 0 且不超过画宽的 0.92。")
    if accent is not None and (not accent or sum(s.count(accent) for s in lines) != 1):
        raise ValueError("请选取在单行标题中出现一次的非空强调词。")
    if len(highlights) > 3 or any(not s.strip() for s in highlights):
        raise ValueError("请将亮点精简为一至三条非空短句。")
    with Image.open(plate) as source:
        canvas = source.convert("RGB")
    w, h = canvas.size
    left = round(w * 0.04)
    y = round(h * 0.05)
    available = round(w * width)
    if digest_mastheads is not None:
        y += draw_digest_mastheads(canvas, digest_mastheads, left, y, available) + round(h * 0.03)
    elif masthead:
        mark = read_masthead(masthead)
        mark_width = min(available, round(w * 0.40)) if description else available
        scale = min(mark_width / mark.width, h * 0.19 / mark.height)
        mark = mark.resize(
            (max(1, round(mark.width * scale)), max(1, round(mark.height * scale))),
            Image.Resampling.LANCZOS,
        )
        canvas.paste(mark, (left, y), mark)
        y += mark.height + round(h * 0.03)

    draw = ImageDraw.Draw(canvas)
    edge = min(w, h)
    font, boxes = fit_text(font_path, lines, available, round(edge * (0.24 if description else 0.14)),
                           round(edge * 0.025))
    size = font.size
    top = min(box[1] for box in boxes)
    bottom = max(box[3] for box in boxes)
    advance = bottom - top + max(1, round(size * 0.07))
    if y + (len(lines) - 1) * advance + bottom - top > h * 0.95:
        raise ValueError("标题超出画面，请减少行数或缩小排字区宽度。")
    for line, box in zip(lines, boxes):
        x = left - box[0]
        baseline = y - top
        draw.text((x, baseline), line, fill=INK, font=font, anchor="ls")
        if accent and accent in line:
            prefix = line.partition(accent)[0]
            # Include pair kerning at the boundary between the two colors.
            offset = font.getlength(prefix + accent[0]) - font.getlength(accent[0])
            draw.text((x + offset, baseline), accent, fill=VIOLET, font=font, anchor="ls")
        y += advance
    if description:
        desc_font, (box,) = fit_text(description_font or text_font or font_path, [description], available,
                                     min(round(edge * 0.052), max(1, size // 2)), round(edge * 0.021))
        baseline = y + round(edge * 0.006) - box[1]
        if baseline + box[3] > h * 0.95:
            raise ValueError("描述超出画面，请精简标题或描述。")
        draw.text((left - box[0], baseline), description, font=desc_font, fill=INK, anchor="ls")
        y = baseline + box[3]
    if highlights:
        small, bounds = fit_text(text_font or font_path, highlights, available, round(edge * 0.032),
                                 round(edge * 0.024))
        ascent = -min(box[1] for box in bounds)
        descent = max(box[3] for box in bounds)
        step = ascent + descent + round(small.size * 0.4)
        baseline = max(y + round(h * 0.03), round(h * 0.69)) + ascent
        if baseline + (len(highlights) - 1) * step + descent > h * 0.95:
            raise ValueError("下方空间不足，请减少亮点行数或调整标题。")
        for highlight, box in zip(highlights, bounds):
            draw_highlight(draw, left - box[0], baseline, highlight, small)
            baseline += step
    # Reserve a new filename so a second pass keeps the previous artwork.
    with output.open("xb") as stream:
        try:
            canvas.save(stream, format="PNG")
        except OSError:
            stream.close()
            output.unlink()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plate", type=Path)
    parser.add_argument("output", type=Path, help="新的 PNG 文件路径")
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--text-font", type=Path, help="用于描述和亮点、覆盖其全部字形的字体")
    parser.add_argument("--description-font", type=Path, help="中文描述专用特粗黑字体，优先于 --text-font")
    parser.add_argument("--description", help="排在特大主标题下的一句短描述")
    parser.add_argument("--line", action="append", required=True)
    parser.add_argument("--width", type=float, default=0.50)
    parser.add_argument("--highlight", action="append", default=[], help="在左下方排一条亮点小字，可重复指定")
    parser.add_argument("--accent")
    headers = parser.add_mutually_exclusive_group()
    headers.add_argument("--masthead", type=Path)
    headers.add_argument("--digest-mastheads", type=Path, nargs=3, metavar=("第一篇", "第二篇", "第三篇"),
                         help="按篇位横排三个原刊字标，刊名之间以留白和竖线分隔")
    args = parser.parse_args()
    try:
        typeset(args.plate, args.output, args.font, args.line, args.width, args.accent, args.masthead,
                args.highlight, args.description, args.text_font, args.description_font, args.digest_mastheads)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
