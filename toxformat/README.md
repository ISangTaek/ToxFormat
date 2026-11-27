# ToxFormat

排版时从「栏目头图与尾图」读取对应栏目头图，所有稿件以统一公众号尾图收尾。论文解析与文献解析、论文速读与文献速读分别共用头图。需要额外的关注引导时，在提示词中写「添加关注我们」。六张正式素材随 Git 仓库、项目包和技能包分发。

「未毒先知」的微信公众号排版技能。将独立技能 ZIP 中的整个 `toxformat` 文件夹放入宿主的技能目录（项目仓库使用根目录安装器），重新加载。已安装独立 gzh-design 的环境，可使用完整项目包中的 `install.py --host codex --migrate` 备份旧入口。宿主也可改成 `claude`、`workbuddy` 或 `dsh`。

附上 Word，输入「对这份文档进行公众号排版」。文献解析提交一份，文献速读提交三份，各占一个位置。文件名使用「栏目-日期-题名」，默认紫罗兰，提示词可指定其他主题。Agent 提取原稿，默认按篇检查 AI 感和错别字，交付报告和排版预览后询问是否进行事实核查。提示词明确要求「进行事实核查」时，随稿核对原始文献。打开预览，点击「复制到公众号」。

完整操作见[技能说明](SKILL.md)。Python 3.9+ 可直接运行脚本；Word 收稿格式为 `.docx`，无需安装 LibreOffice。栏目和主题可按[登记说明](references/catalog-guide.md)继续扩展。

上游排版文档及许可保留于包内。[中文档案](upstream-readme.zh.md) · [English upstream notes](upstream-readme.en.md) · [版权与许可](THIRD-PARTY-NOTICES.md)
