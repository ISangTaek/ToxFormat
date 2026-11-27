# 公众号排版组件库 —— 文献解析-紫罗兰

## 设计变量速查表

| 元素 | 取值 |
|---|---|
| 主色、标题色、正文色 | 紫墨 `#5D4679`，深墨 `#30263E`，正文 `#353039` |
| 色纸、分隔线、辅助文字 | `#F5F1F7`，`#D9CDE1`，`#65576C` |
| 关注条 | 宽 90%，最大 304px，单行排版，上下各 4px 内边距。上下两道细线和一对印刷花叶衬托公众号名称。 |
| 字体与间距 | 章题用宋体或衬线字体，正文 15px、行高 2。关键词为 1px 紫色下划线。 |

## 各组件完整 HTML

关注提示引导读者点击微信正文上方的公众号名称，整条使用静态文字。按语仅在原稿有明确按语或编辑要求添加时插入。普通开篇使用原稿完整首段。数据在正文中按原字号呈现。按实际稿件填入示例文字、署名和图注。

### 刊首关注引导

```html
<section style="box-sizing:border-box;width:90%;max-width:304px;margin:2px auto 22px;padding:4px 2px;text-align:center;background:#FCFAFC;border-top:1px solid #BEABC9;border-bottom:1px solid #DDD3E1;"><p style="margin:0;font-family:Baskerville,Georgia,'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:13px;line-height:22px;letter-spacing:0.2px;color:#55485C;"><span style="font-family:Georgia,'Segoe UI Symbol','Apple Symbols','Noto Sans Symbols 2',serif;font-size:15px;line-height:1;color:#866899;vertical-align:baseline;"><span leaf="">☙</span></span><span style="margin:0 6px;"><span style="font-family:Baskerville,Georgia,'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:13px;color:#795F89;margin-right:3px;"><span leaf="">↑</span></span><span leaf="">点击上方</span><strong style="font-family:Baskerville,Georgia,'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:14px;font-weight:700;color:#563C6D;"><span leaf="">「{{公众号名称}}」</span></strong><span leaf="">关注我们</span></span><span style="font-family:Georgia,'Segoe UI Symbol','Apple Symbols','Noto Sans Symbols 2',serif;font-size:15px;line-height:1;color:#866899;vertical-align:baseline;"><span leaf="">❧</span></span></p></section>
```

### 编者按（有原文或编辑填写时启用）

```html
<section style="padding:12px 14px;margin:0 0 23px;background:#F5F1F7;border-left:2px solid #5D4679;"><p style="margin:0 0 5px;font-size:13px;font-weight:700;color:#5D4679;"><span leaf="">编者按</span></p><p style="margin:0;font-size:15px;line-height:1.8;color:#353039;"><span leaf="">{{按语原文}}</span></p></section>
```

### 普通首段

```html
<p style="margin:0 0 20px;font-family:'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif;font-size:15px;line-height:2;color:#353039;letter-spacing:0.25px;text-align:left;overflow-wrap:break-word;"><span leaf="">{{原稿完整首段}}</span></p>
```

### 正文段落

```html
<p style="margin:0 0 20px;font-family:'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif;font-size:15px;line-height:2;color:#353039;letter-spacing:0.25px;text-align:left;overflow-wrap:break-word;"><span leaf="">{{正文段落}}</span></p>
```

### 正文关键词

```html
<p style="margin:0 0 20px;font-family:'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif;font-size:15px;line-height:2;color:#353039;letter-spacing:0.25px;text-align:left;overflow-wrap:break-word;"><span leaf="">正文中的</span><span style="color:#30263E;font-weight:600;border-bottom:1px solid #5D4679;"><span leaf="">关键概念</span></span><span leaf="">使用细线标示，读者可以沿着原句阅读。</span></p>
```

### 原稿加粗

```html
<p style="margin:0 0 20px;font-family:'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif;font-size:15px;line-height:2;color:#353039;letter-spacing:0.25px;text-align:left;overflow-wrap:break-word;"><span leaf="">示例段落包含</span><strong style="color:#30263E;font-weight:700;"><span leaf="">原作者加粗的字词</span></strong><span leaf="">以及后续正文。</span></p>
```

### 一级章题

```html
<section style="margin:38px 0 21px;text-align:center;"><p style="margin:0 0 3px;font-family:Baskerville,Georgia,'Times New Roman',serif;font-size:11px;font-weight:600;letter-spacing:2px;line-height:1.4;color:#5D4679;"><span leaf="">{{英文章签}}</span></p><h3 style="font-family:'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:21px;letter-spacing:1px;font-weight:600;line-height:1.5;color:#30263E;margin:0;"><span leaf="">{{章节标题}}</span></h3><section style="width:30px;height:0;line-height:0;border-top:1px solid #5D4679;margin:9px auto 0;"><span leaf=""><br></span></section></section>
```

### 左竖线小标题

```html
<h4 style="font-family:'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif;margin:24px 0 12px;padding:1px 0 1px 11px;border-left:2px solid #9A82A8;color:#30263E;font-size:16px;line-height:1.55;font-weight:700;"><span leaf="">{{小节标题}}</span></h4>
```

### 章节分割线

```html
<section style="height:0;line-height:0;font-size:0;border-top:1px solid #D9CDE1;margin:22px 0;"><span leaf=""><br></span></section>
```

### 原文直接引语

```html
<section style="background:#F5F1F7;border-left:2px solid #5D4679;padding:13px 16px;"><p style="color:#5D4679;font-weight:700;font-size:14px;line-height:1.55;margin:0 0 5px;"><span leaf="">原文引述</span></p><p style="font-family:'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:16px;line-height:1.8;color:#30263E;margin:0;"><span leaf="">{{引语原文}}</span></p></section>
```

### 术语释义

```html
<p style="font-size:14px;line-height:1.8;margin:0;padding:6px 0;border-bottom:1px solid #D9CDE1;"><strong style="font-weight:700;color:#5D4679;margin-right:10px;"><span leaf="">术语</span></strong><span leaf="">术语定义占位。</span></p>
```

### 研究局限

```html
<section style="background:#F5F1F7;border-left:2px solid #5D4679;padding:13px 16px;"><p style="color:#5D4679;font-weight:700;font-size:14px;line-height:1.55;margin:0 0 5px;"><span leaf="">研究局限</span></p><p style="font-size:14px;line-height:1.8;color:#353039;margin:0;"><span leaf="">样本范围或方法局限占位。</span></p></section>
```

### 并列条目

```html
<section><p style="margin:4px 0;color:#353039;font-size:14px;line-height:1.75;"><span style="color:#5D4679;font-size:13px;font-weight:600;margin-right:8px;"><span leaf="">•</span></span><span leaf="">第一项内容占位</span></p><p style="margin:4px 0;color:#353039;font-size:14px;line-height:1.75;"><span style="color:#5D4679;font-size:13px;font-weight:600;margin-right:8px;"><span leaf="">•</span></span><span leaf="">第二项内容占位</span></p></section>
```

### 顺序条目

```html
<section><p style="margin:4px 0;color:#353039;font-size:14px;line-height:1.75;"><span style="color:#5D4679;font-size:13px;font-weight:600;margin-right:8px;"><span leaf="">1.</span></span><span leaf="">第一项内容占位</span></p><p style="margin:4px 0;color:#353039;font-size:14px;line-height:1.75;"><span style="color:#5D4679;font-size:13px;font-weight:600;margin-right:8px;"><span leaf="">2.</span></span><span leaf="">第二项内容占位</span></p></section>
```

### 参数表

```html
<table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#F5F1F7;"><th style="text-align:left;padding:7px 9px;border-bottom:1px solid #D9CDE1;font-size:13px;line-height:1.6;"><span leaf="">参数</span></th><th style="text-align:left;padding:7px 9px;border-bottom:1px solid #D9CDE1;font-size:13px;line-height:1.6;"><span leaf="">取值</span></th></tr></thead><tbody><tr><td style="text-align:left;padding:7px 9px;border-bottom:1px solid #D9CDE1;font-size:13px;line-height:1.6;"><span leaf="">参数名称占位</span></td><td style="text-align:left;padding:7px 9px;border-bottom:1px solid #D9CDE1;font-size:13px;line-height:1.6;"><span leaf="">数值占位</span></td></tr><tr><td style="text-align:left;padding:7px 9px;border-bottom:1px solid #D9CDE1;font-size:13px;line-height:1.6;"><span leaf="">参数名称占位</span></td><td style="text-align:left;padding:7px 9px;border-bottom:1px solid #D9CDE1;font-size:13px;line-height:1.6;"><span leaf="">数值占位</span></td></tr></tbody></table>
```

### 正文插图

```html
<section style="margin:19px 0 25px;"><span leaf=""><img alt="{{图片替代文字}}" src="{{%E5%9B%BE%E7%89%87%E5%9C%B0%E5%9D%80}}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
```

### 带图注图版

```html
<section style="margin:19px 0 25px;"><span leaf=""><img alt="{{图片替代文字}}" src="{{%E5%9B%BE%E7%89%87%E5%9C%B0%E5%9D%80}}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span><p style="margin:8px 0 0;color:#65576C;text-align:center;font-size:12px;line-height:1.65;"><strong style="font-weight:700;color:#5D4679;"><span leaf="">{{图号}}</span></strong><span leaf="">　{{原始图注}}</span></p></section>
```

### 浅底代码段

```html
<section style="padding:13px 16px;background:#F5F1F7;color:#30263E;border-left:2px solid #5D4679;"><p style="font-family:'IBM Plex Mono',Consolas,monospace;font-size:13px;line-height:1.7;margin:0;"><span leaf="">model_name</span></p><p style="font-family:'IBM Plex Mono',Consolas,monospace;font-size:13px;line-height:1.7;margin:0;"><span leaf="">  parameter</span></p></section>
```

### 文献引注

```html
<p style="font-size:14px;line-height:1.8;margin:0;padding:6px 0;border-bottom:1px solid #D9CDE1;"><strong style="font-weight:700;color:#5D4679;margin-right:10px;"><span leaf="">文献</span></strong><span leaf="">作者、期刊与出版信息占位。</span></p>
```

### 阅读原文引导

```html
<p style="font-size:14px;line-height:1.8;margin:0;padding:6px 0;border-bottom:1px solid #D9CDE1;"><strong style="font-weight:700;color:#5D4679;margin-right:10px;"><span leaf="">阅读原文</span></strong><a href="{{论文URL}}" style="color:#5D4679;text-decoration:underline;overflow-wrap:anywhere;"><span leaf="">{{论文URL}}</span></a></p>
```

### 文末署名

```html
<p style="font-size:12px;line-height:1.65;color:#65576C;margin:6px 0;"><span leaf="">作者：{{作者名}}</span></p>
```

### 转载须知

```html
<section style="background:#F5F1F7;border-left:2px solid #5D4679;padding:13px 16px;"><p style="color:#5D4679;font-weight:700;font-size:14px;line-height:1.55;margin:0 0 5px;"><span leaf="">转载须知</span></p><p style="font-size:14px;line-height:1.8;color:#353039;margin:0;"><span leaf="">{{转载要求原文}}</span></p></section>
```

### END 收尾

```html
<section style="margin:32px 0 0;display:flex;align-items:center;justify-content:center;"><section style="width:36px;height:0;line-height:0;border-top:1px solid #D9CDE1;"><span leaf=""><br></span></section><span style="margin:0 14px;font-family:Baskerville,Georgia,'Times New Roman',serif;font-size:13px;letter-spacing:3px;color:#5D4679;"><span leaf="">END</span></span><section style="width:36px;height:0;line-height:0;border-top:1px solid #D9CDE1;"><span leaf=""><br></span></section></section>
```

## 完整文章模板骨架

```html
<section style="box-sizing:border-box;max-width:677px;margin:0 auto;padding:4px 14px 20px;background:#FFFFFF;font-family:'Microsoft YaHei','PingFang SC',sans-serif;color:#353039;">
  <!-- 刊首关注引导；按实际公众号名填入 -->
  <!-- 可选编者按；有按语时插入，无内容时省略整个组件 -->
  <!-- 完整首段、前言正文、原稿插图 -->
  <!-- 文章各章：居中章题、正文、左竖线小标题、原图与图注 -->
  <!-- 结论、分割线、转载须知、原稿名片、署名、论文链接 -->
  <!-- END，正文最后一个组件 -->
</section>
```

标题、平台署名和封面在微信发布字段中填写。按原稿保留研究数字、配图、图注和署名。图注与插图相邻。省略自动导读、开头摘句和放大数据卡。

## 文章类型 → 组件组合配方表

| 稿件 | 主体结构 |
|---|---|
| 论文解析 | 背景原段、方法、分节结果与图注、结论、署名与论文链接 |
| 研究简报 | 普通开篇、研究设计、结果段落或原始数据表、局限与结论 |
| 学术评论 | 普通开篇、论点小节、原文引语、文献引注 |

## Markdown → 组件映射规则表

| 来源 | 组件 |
|---|---|
| 公众号名称 | 文首窄幅关注条 |
| 明确标注的编者按、编辑指定的按语 | 编者按 |
| 普通首段、普通正文 | 完整原段 |
| 二级、三级标题 | 居中章题、左竖线小标题 |
| 加粗及关键词 | 原稿加粗、正文关键词 |
| 原文引语、表格、编号或并列事项 | 原文直接引语、参数表、顺序或并列条目 |
| 图片及原始图号 | 正文插图或带图注图版 |
| 分隔线 | 章节分割线 |
| 文末原有署名、转载说明、链接 | 转载须知、署名及阅读原文，最后为 END |
