# ToxFormat

「未毒先知」的微信公众号排版技能。将整个 `toxformat` 文件夹放入宿主的技能目录，重新加载。已安装独立 gzh-design 的环境，可使用完整项目包中的 `install.py --host codex --migrate` 备份旧入口。宿主也可改成 `claude`、`workbuddy` 或 `dsh`。

附上 Word，输入「对这份文档进行公众号排版」。文献解析提交一份，文献速读提交三份，各占一个位置。文件名使用「栏目-日期-题名」，默认紫罗兰，提示词可指定其他主题。Agent 提取原稿，按篇完成文风、错别字和文献事实检查，先交付参考报告，随后生成预览。打开预览，点击「复制到公众号」。

完整操作见[技能说明](SKILL.md)。Python 3.9+ 可直接运行脚本；处理旧版 `.doc` 时使用 LibreOffice。栏目和主题可按[登记说明](references/catalog-guide.md)继续扩展。

上游排版文档及许可保留于包内。[中文档案](upstream-readme.zh.md) · [English upstream notes](upstream-readme.en.md) · [版权与许可](THIRD-PARTY-NOTICES.md)
