# 文献速读-紫罗兰

基于「文献解析-紫罗兰」。适用于一则或多则论文的短篇连读。

## 设计变量速查表

| 部位 | 规则 |
|---|---|
| 刊首与文末 | 紫墨主色 #5D4679，窄幅花叶关注条，末尾细线 END |
| 逐篇标题 | 左对齐 21px 宋体，12px 篇序随本稿条目数量生成 |
| 正文强调 | 正文关键词用常规字重；仅开头概括整项研究的总述句及后文的主要结果句用主题紫色（#5D4679）加粗。单稿优先两句，三篇合刊合计最多三句。原稿加粗记录在复验清单。期刊名称用黑色加粗斜体。 |
| 文献信息 | 期刊与原稿所列影响因子同排，日期和团队另起一行，以浅紫竖线归组 |
| 速读段落 | 15px 正文，行高 1.9，紫色行内字段名与正文同读 |
| 原文入口 | 网址可点击并换行，二维码按原稿逐篇配对，显示宽度 84px |

## 各组件完整 HTML

### 刊首关注提示

```html
<section style="box-sizing:border-box;width:90%;max-width:304px;margin:2px auto 22px;padding:4px 2px;text-align:center;background:#FCFAFC;border-top:1px solid #BEABC9;border-bottom:1px solid #DDD3E1;"><p style="margin:0;font-family:Baskerville,Georgia,'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:13px;line-height:22px;letter-spacing:0.2px;color:#55485C;"><span style="font-family:Georgia,'Segoe UI Symbol','Apple Symbols','Noto Sans Symbols 2',serif;font-size:15px;line-height:1;color:#866899;vertical-align:baseline;"><span leaf="">☙</span></span><span style="margin:0 6px;"><span style="font-family:Baskerville,Georgia,'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:13px;color:#795F89;margin-right:3px;"><span leaf="">↑</span></span><span leaf="">点击上方</span><strong style="font-family:Baskerville,Georgia,'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:14px;font-weight:700;color:#563C6D;"><span leaf="">「{{公众号名称}}」</span></strong><span leaf="">关注我们</span></span><span style="font-family:Georgia,'Segoe UI Symbol','Apple Symbols','Noto Sans Symbols 2',serif;font-size:15px;line-height:1;color:#866899;vertical-align:baseline;"><span leaf="">❧</span></span></p></section>
```

### 可选编者按

```html
<section style="padding:12px 14px;margin:0 0 23px;background:#F5F1F7;border-left:2px solid #5D4679;"><p style="margin:0 0 5px;font-size:13px;font-weight:700;color:#5D4679;"><span leaf="">编者按</span></p><p style="margin:0;font-size:15px;line-height:1.8;color:#353039;"><span leaf="">{{按语原文}}</span></p></section>
```

### 篇序与论文标题

```html
<section style="margin:0 0 10px;"><p style="margin:0 0 5px;color:#725781;font-size:12px;line-height:1.5;letter-spacing:1.2px;font-family:Baskerville,Georgia,'Times New Roman',serif;"><span style="display:inline-block;width:21px;height:0;border-top:1px solid #A48CAF;vertical-align:middle;margin-right:8px;"><span leaf=""><br></span></span><span leaf="">{{篇序}} / {{篇数}}</span></p><h3 style="margin:0;font-family:'Noto Serif SC','Songti SC','STSong','SimSun',serif;font-size:21px;font-weight:700;color:#30263E;line-height:1.55;"><span leaf="">{{论文短标题}}</span></h3></section>
```

### 文献信息

```html
<section style="margin:0 0 18px;padding:7px 0 7px 11px;border-left:2px solid #BEABC9;"><p style="margin:0;color:#493453;font-size:15px;font-family:Baskerville,Georgia,'Times New Roman',serif,serif;line-height:1.5;"><strong style="color:#000000;font-weight:700;font-style:italic;"><span leaf="">{{期刊名}}</span></strong><span style="font-size:12px;"><span leaf="">{{期刊附注}}</span></span></p><p style="margin:2px 0 0;font-size:12px;line-height:1.65;color:#65576C;"><span leaf="">{{日期}}</span><span leaf="">　·　</span><span leaf="">{{团队}}</span></p></section>
```

### 速读段落

```html
<p style="margin:0 0 14px;font-size:15px;line-height:1.9;color:#353039;letter-spacing:0.2px;overflow-wrap:break-word;"><span leaf="">{{字段}}：</span>{{段落富文本}}</p>
```

### 原稿图版

```html
<section style="margin:19px 0 25px;"><span leaf=""><img alt="{{图片替代文字}}" src="{{图片地址}}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span><p style="margin:8px 0 0;color:#65576C;text-align:center;font-size:12px;line-height:1.65;"><strong style="font-weight:700;color:#5D4679;"><span leaf="">{{图号}}</span></strong><span leaf="">{{原始图注}}</span></p></section>
```

### 逐篇原文入口

```html
<section style="display:flex;align-items:center;margin:17px 0 0;padding:10px 12px;background:#F7F4F8;border-top:1px solid #E1D8E6;"><section style="flex:1;min-width:0;padding-right:10px;"><p style="margin:0 0 3px;font-size:13px;font-weight:700;color:#5D4679;"><span leaf="">原文链接：</span></p><p style="margin:0;font-size:12px;line-height:1.65;overflow-wrap:anywhere;word-break:break-all;"><a href="{{原文网址}}" style="color:#56475E;text-decoration:underline;"><span leaf="">{{原文网址}}</span></a></p></section><section style="width:91px;flex:0 0 91px;text-align:center;"><span leaf=""><img alt="{{二维码说明}}" src="{{二维码地址}}" style="display:block;width:84px;max-width:100%;height:auto;margin:0 auto;"></span><p style="margin:3px 0 0;font-size:10px;line-height:1.5;color:#65576C;"><span leaf="">{{扫码说明}}</span></p></section></section>
```

### 篇间分隔

```html
<section style="height:0;line-height:0;font-size:0;border-top:1px solid #D9CDE1;margin:29px 0 23px;"><span leaf=""><br></span></section>
```

### 转载须知

```html
<section style="background:#F5F1F7;border-left:2px solid #5D4679;padding:13px 16px;"><p style="color:#5D4679;font-weight:700;font-size:14px;line-height:1.55;margin:0 0 5px;"><span leaf="">转载须知</span></p><p style="font-size:14px;line-height:1.8;color:#353039;margin:0;"><span leaf="">{{转载要求原文}}</span></p></section>
```

### 公众号名片

```html
<section style="margin:19px 0 25px;"><span leaf=""><img alt="{{图片替代文字}}" src="{{图片地址}}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
```

### 文末署名

```html
<p style="font-size:12px;line-height:1.65;color:#65576C;margin:6px 0;"><span leaf="">作者：{{作者名}}</span></p>
```

### END

```html
<section style="margin:32px 0 0;display:flex;align-items:center;justify-content:center;"><section style="width:36px;height:0;line-height:0;border-top:1px solid #D9CDE1;"><span leaf=""><br></span></section><span style="margin:0 14px;font-family:Baskerville,Georgia,'Times New Roman',serif;font-size:13px;letter-spacing:3px;color:#5D4679;"><span leaf="">END</span></span><section style="width:36px;height:0;line-height:0;border-top:1px solid #D9CDE1;"><span leaf=""><br></span></section></section>
```

## 完整文章模板骨架

```html
<section style="box-sizing:border-box;max-width:677px;margin:0 auto;padding:4px 14px 20px;background:#FFFFFF;font-family:'Microsoft YaHei','PingFang SC',sans-serif;color:#353039;">
  <!-- 关注提示；原稿有按语或编辑指定时在此加入按语 -->
  <!-- 循环实际论文条目：篇序及标题、文献信息、速读段落、原图图注、原文入口 -->
  <!-- 相邻条目用篇间分隔；网址与二维码仅取自当前条目 -->
  <!-- 分隔线、原稿的转载说明与名片、署名、END -->
</section>
```

## 文章类型 → 组件组合配方表

正式合刊一次提交三份不同的 Word，每份独占一个篇位。保留编辑指定顺序或附件顺序，各篇的原文入口与二维码跟随本篇处理。

| 稿件 | 处理 |
|---|---|
| 多篇连读 | 按原稿顺序逐篇渲染。每篇完整呈现研究要点与来源后，再起下一篇。 |
| 单篇速读 | 使用同一信息条和速读段落，省略篇间分隔及篇序分母。 |
| 稿件字段有缺项 | 按实有字段排版，随字段一起去掉对应的标点、分隔符和容器。只有链接时保留文字入口，只有二维码时保留二维码和原稿说明。 |

## Markdown → 组件映射规则表

| 原稿内容 | 对应位置 |
|---|---|
| 总标题与推文作者 | 微信标题栏及署名；全文预览与正文复制区域分开 |
| 论文短标题 | 篇序与论文标题 |
| 期刊、IF、发表日期、团队 | 文献信息，逐项沿用原稿 |
| 带标签的段落 | 对应的速读段落；保留标签及原文顺序 |
| 图、图号与图注 | 紧随所属论文内容，保持原稿图号 |
| 原文网址和二维码 | 各篇末尾原文入口 |
| 转载说明、名片、署名 | 全文末尾出现一次，随后为 END |
