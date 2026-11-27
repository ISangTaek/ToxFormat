#!/usr/bin/env python3
"""把已校验的公众号正文片段（纯 <section>）包成带「复制」按钮的浏览器预览页。

用户打开预览页 → 点右上角「复制到公众号」→ 按钮选中并复制里面渲染后的富文本
（等价手动 Ctrl+A/Ctrl+C，样式全保留）→ 到公众号编辑器 Ctrl+V 粘贴即可。

按钮和 JS 只存在于预览外壳里，**不在被复制的 section 内**，所以粘进公众号的
仍是干净合规的正文，不含 <script>/<button>。校验请对原始 section 文件跑
validate_gzh_html.py（本预览页含 script/style，不参与校验）。

用法:
    wrap_preview.py <section.html> [output.html]
    默认输出 <section去扩展名>_预览.html
"""

import argparse
import html
import re
from pathlib import Path
from publication_art import artwork, FOOTER, FOLLOW
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="将通用稿正文与栏目素材装配成可复制预览")
    parser.add_argument("src", type=Path)
    parser.add_argument("out", nargs="?", type=Path)
    parser.add_argument("--column", help="栏目名，默认读取源文件名前缀")
    parser.add_argument("--follow", action="store_true", help="加入刊首关注引导")
    parser.add_argument("--body-out", type=Path, help="完整正文输出路径")
    args = parser.parse_args()
    src = args.src
    content = src.read_text(encoding="utf-8-sig").strip()
    if 'alt="' + FOOTER[:-4] + '"' not in content:
        match = re.fullmatch(r"(<section\b[^>]*>)(.*)(</section>)", content, re.S)
        if not match:
            parser.error("正文需要一个完整的 section 容器。")
        header, footer = artwork(args.column or src.stem)
        content = match[1] + header + (FOLLOW if args.follow else "") + match[2] + footer + match[3]
    body_out = args.body_out or src.with_name(src.stem + "_正文.html")
    body_out.write_text(content, encoding="utf-8")
    print("完整正文：" + str(body_out))
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "assets", "preview-template.html")
    tpl = open(tpl_path, encoding="utf-8").read()

    title = os.path.splitext(os.path.basename(src))[0]
    out_html = tpl.replace("{{TITLE}}", html.escape(title)).replace("<!--GZH_CONTENT-->", content)

    out = args.out or os.path.splitext(src)[0] + "_预览.html"
    open(out, "w", encoding="utf-8").write(out_html)
    print(f"✓ 已生成带「复制」按钮的预览页: {out}")
    print("  用浏览器打开它，点右上角「复制到公众号」，再去公众号编辑器 Ctrl/⌘+V 粘贴。")


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
