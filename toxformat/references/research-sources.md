# AI 感预警的 GitHub 调研

2026-11-27 核对以下仓库的固定提交。ToxFormat 将文风线索整理成可定位的句级规则，并为本号自定计分公式及大修参考线。规则和阈值的调整应同步更新版本，便于复验旧稿。

| 项目 | 用于首版的观察 | 查阅的固定版本 |
| --- | --- | --- |
| Humanizer-zh | 抽象词堆叠、夸张收尾、对话残留；识别“闭环反馈”等专业搭配 | [中文规则](https://github.com/op7418/Humanizer-zh/blob/f4518a8eab97b8bfebc66a89d34320a89bef6930/SKILL.md) |
| humanizer | 正文中残留的聊天答复、过度宣称重要性 | [英文规则](https://github.com/blader/humanizer/blob/a32f24407364c74c812b43c15926d638bee1e072/SKILL.md) |
| Academic-Humanizer | 反复使用的揭题和翻转句式；考察相邻句的重复 | [学术写作规则](https://github.com/junbolian/Academic-Humanizer/blob/62b0a02627e063015466c70f0a4dd4929a9f7f5b/academic-humanizer/references/chinese.md) |
| zh-scientific-humanizer | 中文科研写作中的意义宣示、密集连接词与科学语境 | [科研表达案例](https://github.com/XuanjinZhu/zh-scientific-humanizer/blob/40b4721c3ecec7bae1746901e58d19210d0f4815/references/zh-scientific-ai-patterns.md) |
| zh-paper-polish | 项目统计的 165 篇已发表中文论文中，49 篇使用过“值得注意的是”，47 篇使用过“综上所述”。据此将单次连接词排除在评分外 | [语料统计](https://github.com/DawnJson/zh-paper-polish/blob/04ca316721680aea92dbc67b6cf34aae7f2913b3/references/human-baseline.md) |

前四个项目的公开许可与署名随包保存。zh-paper-polish（CC BY-NC-SA 4.0）仅作为上述发表语料统计的来源。本包词表、公式和代码独立编写。[第三方声明](../THIRD-PARTY-NOTICES.md)
