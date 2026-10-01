# 笔记输入格式（词条 JSON）

`scripts/build_note.py` 只吃这一种格式。所有文本字段都是非空纯文本，不能夹 HTML 标记；字符串数组会去重（保持首次出现顺序）。数据 JSON 只是中间文件，最终交付的 HTML 不依赖它。

```json
{
  "show": "剧名",
  "episode": "S01E01",
  "subtitle_source": "用户提供 subtitle.srt / 检索自 xxx",
  "level": "高中（词汇量约 3500）",
  "lead": "一句话导读：本集主要场景与话题，不剧透结局。",
  "flag": "可选说明：材料不足、用了默认值等",
  "vocab": [ { …词条… } ],
  "phrases": [ { …词条… } ],
  "grammar": [ { …语法点… } ],
  "culture": [ { …文化注… } ]
}
```

## 顶层字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `show` `episode` `subtitle_source` `lead` | 是 | 非空字符串。`lead` 一句话导读，不剧透结局 |
| `level` | 否 | 默认 `高中（词汇量约 3500）` |
| `flag` | 否 | 说明用了默认值、材料不足等；无则留空或不写 |
| `vocab` `phrases` | 二者至少一个非空 | 词条数组，结构相同，只是 `band` 默认值不同 |
| `grammar` `culture` | 否 | 可为空数组或整体省略 |

## 词条（vocab / phrases 共用）

必填六个：`term` `ipa`（美式）`pos` `meaning`（结合剧中语境，不照抄词典）`sentence`（剧中原句）`translation`。

可选：

| 字段 | 类型 | 说明 |
|---|---|---|
| `speaker` `timecode` `context` `mnemonic` | 字符串 | 说话人、时间点（回看锚点）、一句情境说明、记忆点 |
| `collocations` `derivatives` `synonyms` | 字符串数组 | 搭配 / 派生 / 近反义，逐条一条 |
| `targets` | 字符串数组 | 原句加粗定位，见下节；默认 `[term]` |
| `band` | 字符串 | `超纲实词` / `短语搭配` / `俚语口语` / `派生词` 之一；vocab 默认 `超纲实词`，phrases 默认 `短语搭配` |
| `freq` | 整数 ≥1 | 本集出现频次，默认 1；大于 1 时笔记里显示"本集出现 N 次" |

`vocab` 与 `phrases` 合并后按 `term` 去重（不区分大小写），重复收录直接报错。

## targets：原句定位

- 每个 target 用词边界匹配原句（不区分大小写），所有匹配位置一起加粗。
- target 必须逐字出现在 `sentence` 里，否则报错；多个 target 的匹配区间不得重叠。
- 词形变化或短语被宾语拆开时写实际词形，如原句 "They pulled it off" 配 `"targets": ["pulled", "off"]`。**不要改原句来迁就词条。**
- 避免短且在句中重复出现的片段（如单写 `"off"`），会把不相干的位置一起加粗。

## 语法点（grammar）

- 必填：`point`（点题）`rule`（规则说明）。
- 可选：`sentence`（原句）`translation` `speaker` `timecode`；`bad` 与 `good` 必须成对出现，只给一个报错。
- `highlight`（字符串数组）：定位规则同 `targets`，会分别在 `sentence` 和 `good` 里查找，找不到即报错。

## 文化注（culture）

- 必填：`term` `note`（一两句背景说明）。
- 可选：`sentence` `speaker` `timecode`。

## 校验失败怎么办

脚本对每个词条给出「kind 第 N 条 · 字段名」格式的报错。只修报错那一项再跑，不要改脚本绕过校验，也不要删掉报错的词条凑合——删词条会让笔记缺内容，应该修数据。
