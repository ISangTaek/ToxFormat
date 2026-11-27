"""Check the last substantive paragraphs for an actual reuse policy."""

import re
from html.parser import HTMLParser


REMINDER = "请编辑在文末补充转载声明，说明是否允许转载及授权方式。"
POLICY = re.compile(
    r"(?:未经|禁止|谢绝|不得|严禁|允许|欢迎|授权|许可|可以|可自由|请勿|拒绝).{0,24}(?:转载|转发|转摘|转刊)"
    r"|(?:转载|转发|转摘).{0,24}(?:注明|授权|联系|许可|同意|允许|禁止|署名)"
)
FOOTER = re.compile(
    r"^(?:END$|[—─━\s]+$|(?:推文)?(?:撰稿|作者|编辑|审核|排版|来源|原文(?:链接)?|DOI)\s*[：:]"
    r"|https?://|点击.{0,5}(?:原文|文章)|扫.{0,12}(?:二维码|原文)|转载须知$|转载声明$|版权声明$)", re.I
)


def has_notice(paragraphs):
    for text in reversed(list(paragraphs)):
        text = text.strip()
        if not text or FOOTER.match(text):
            continue
        if POLICY.search(text):
            return True
        # Allow a trailing copyright attribution below the policy.
        if not re.match(r"^(?:©|版权所有|版权归)", text):
            break
    return False


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in ("p", "section", "li", "div", "h2", "h3", "h4", "footer"):
            text = "".join(self.parts).strip()
            if text:
                self.lines.append(text)
            self.parts.clear()
