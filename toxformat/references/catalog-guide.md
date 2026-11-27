# 栏目与主题入库

运行时读取 [catalog.json](../assets/catalog.json)，其中 `columns` 定义文件名前缀、默认主题和补充强调规则，`themes` 定义显示名、别名、模板、配色和版本。[主题索引](theme-index.md)供编辑选阅。

- **新增主题。** 根据[主题生成器](theme-generator.md)生成预览，放在 `assets/theme-previews/`。编辑确认后，新建 `references/theme-标识.md`，按现有组件格式写设计变量、完整 HTML、组装骨架、场景配方和映射规则。将名称、唯一标识、版本、组件路径、布局和正文下划线 CSS 同步登记到目录和索引。专属布局用 `folio` 或 `digest`，通用布局用 `editorial`。主题组件里的变量使用已注册同类组件的变量名。修改渲染规则时增加主题或包版本。
- **新增栏目。** 添加唯一前缀、默认主题标识、`structure`（单篇 `analysis` 或三篇合刊 `digest`）、`terms` 和 `max_emphasis`。可直接复用现有结构；新的版式结构需添加对应的段落映射及回归样例。
- **强调位置。** 原稿加粗、斜体、下划线、上下标、链接、颜色和高亮随稿保留。补充强调只在正文、速读的带标签段落或列表中添加。优先栏目词，再取数值单位组合、英文缩写或模型名。同类候选按位置从前到后、同一位置从长到短取用，跳过已标记范围和重复词，达到每段上限后停止。清单的 `start/end` 是段内 Unicode 字符的左闭右开区间。
- **验证。** 先在项目根目录运行下列命令，再用选定样稿检查第一段、小标题、图注、复制区域及新增样式。提交时保留对应的规则版本和样稿正文校验值。

```sh
python toxformat/scripts/toxformat.py themes
python toxformat/scripts/component_lint.py toxformat
python -m unittest discover -s tests
```
