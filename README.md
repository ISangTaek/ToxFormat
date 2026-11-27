# ToxFormat

「未毒先知」公众号的审稿与排版技能。附上 Word，输入 **对这份文档进行公众号排版**。ToxFormat 先交付稿前参考报告，再按投稿原文生成可复制到微信公众平台的富文本。

| 栏目 | 正式收稿 | 默认主题 |
| --- | --- | --- |
| 文献解析 | 一份 `文献解析-日期-题名.docx` | 文献解析-紫罗兰 |
| 文献速读 | 三份 `文献速读-日期-题名.docx`，各占一个篇位，合成一篇推文 | 文献速读-紫罗兰 |

编辑点名主题时，采用提示词中的主题；文件名前缀不明确时，Agent 询问栏目。速读按编辑指定的顺序排，否则沿用附件顺序。稿件顺序不可见时，再请编辑指出顺序。各篇保留自己的署名、图注、原文链接和二维码。没有指定合刊标题时，预览用首篇题名和篇数生成标题。

## 安装

解压完整项目包或克隆本仓库，在含 `install.py` 的目录运行。标准排版仅需 Python 3.9+ 标准库。Word 稿件采用 .docx，无需安装 LibreOffice。

```sh
python install.py --host codex --migrate
```


| 宿主 | 安装参数 | 技能位置 |
| --- | --- | --- |
| Codex | `--host codex` | `$CODEX_HOME/skills`，默认 `~/.codex/skills` |
| Claude Code | `--host claude` | `~/.claude/skills` |
| WorkBuddy | `--host workbuddy` | `~/.workbuddy/skills`；也可在宿主导入技能包 |
| DeepSeek Harness（dsh） | `--host dsh` | `$DSH_HOME/skills`，默认 `~/.dsh/skills` |
| 自定义路径或项目级技能 | `--skills-dir "实际技能目录"` | 安装到指定目录下的 `toxformat/` |

选择宿主实际读取的一处技能目录。若旧 `gzh-design` 安装在同一目录，`--migrate` 将其连同原有主题迁移到技能目录外，并打印备份路径；已安装版本升级时也先备份本地改动。恢复旧版时，将当前 `toxformat` 移到技能目录外，将备份的 `gzh-design` 放回原技能目录，然后重新加载技能。若同一宿主另有项目级旧入口，可在其技能设置中停用。安装完成后开启新会话。

`dist/ToxFormat-1.0.0.zip` 可用于技能导入。`dist/ToxFormat-project-1.0.0.zip` 含安装程序、全部源代码和跨机测试稿。宿主负责发现技能和查阅文献，所有模型调用同一套本地排版脚本。[Codex](https://learn.chatgpt.com/docs/build-skills) · [Claude Code](https://code.claude.com/docs/en/skills) · [WorkBuddy](https://cloud.tencent.com/document/product/1831/134432) · [dsh](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.zh.md)

## 编辑使用

- **文献解析**　附一份 Word，说「对这份文档进行公众号排版」。
- **文献速读**　一次附三份 Word。可说「对这份文档进行公众号排版。第一篇 Z，第二篇 A，第三篇 M」。原始论文 PDF 或补充材料可以一同附上，用于逐篇核查。
- **点名主题**　「对这三份速读稿进行公众号排版，使用石墨极简风」。原名称「论文速读-紫罗兰」映射到正式主题「文献速读-紫罗兰」。
- **稿前报告**　AI 感按篇计分，达到 50/100 提示建议大修。错别字给出原句位置和建议用字。排版完成后，Agent 会询问是否对照原始文献进行事实核查。需要随稿核查时，在排版提示词中写「进行事实核查」。报告交付后直接排版，正文采用编辑提交的原稿。[评分及核查规则](toxformat/references/editorial-review.md) · [GitHub 调研来源](toxformat/references/research-sources.md)
- **复制到微信**　打开 `预览.html`，点击「复制到公众号」，粘贴到微信正文框。标题和封面单独设置。默认本地预览内嵌图片；如微信编辑器过滤了本地图片，可在编辑器上传该图片，已有素材 HTTPS 地址时也可通过 `--image-map` 重新生成。
- **新主题**　描述风格或提供参考图，预览确认后入库。现有八套主题、通用组件、历史图库及主题生成器随包提供。[可选主题](toxformat/references/theme-index.md) · [主题和栏目扩展](toxformat/references/catalog-guide.md)

## 跨机复验

[复验样稿与预期结果](tests/README.md)含三份不同的 Word、两份模拟原文和一份用于测试格式拒收的旧版 Word。在另一台电脑使用相同包版本、相同附件顺序、相同主题。比较 `复验清单.json` 的 `body_sha256`、按篇图像顺序、`word_marks` 与 `added_emphasis`，可核对正文 HTML 及每个强调片段。证据状态与审稿结果只进入报告和清单。

```sh
python -m unittest discover -s tests -v
python -m unittest discover -s toxformat/scripts -p test_validate_gzh_html.py
python toxformat/scripts/component_lint.py toxformat
python tools/package.py
```

完整的 Agent 操作步骤及通用排版入口见[技能说明](toxformat/SKILL.md)。排版引擎在甲木、摸鱼小李的 gzh-design 上继续开发，全包采用 AGPL-3.0-or-later。[许可证](LICENSE) · [上游与第三方声明](toxformat/THIRD-PARTY-NOTICES.md)
