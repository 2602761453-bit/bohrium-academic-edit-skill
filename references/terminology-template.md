# 术语表模板

## 生成规则

1. 每篇稿件**只建一张**术语表，第 1 步冻结，后续只引用不新增（新增项标 `added_late: true`）。
2. 冲突时以**原文多数用法**为准；少数派写法记入 `conflict`，不改原文、只在 `uncertainty` 提示。
3. 缩写：`FEV1` 与 `FEV-1` 视为同一术语的变体；首次出现必须展开全称（若原文未展开且无法从材料推断，记 `uncertainty`，**不要凭常识补全称**）。
4. 大小写与连字符属于术语的一部分：`state-of-the-art` 与 `state of the art` 算变体，不算错别字。
5. 中英混排稿：同一概念的中文与英文各记一行，`lang` 区分。

## 字段

```json
{
  "canonical": "FEV1",
  "lang": "en",
  "variants": ["FEV-1", "fev1"],
  "occurrences": [
    {"location": "§1 ¶2 s3", "as_written": "FEV-1"},
    {"location": "§2 ¶1 s1", "as_written": "FEV1"}
  ],
  "first_occurrence": "§1 ¶2 s3",
  "abbreviation": {"is_abbreviation": true, "expanded": "forced expiratory volume in 1 second", "defined_at": null},
  "unified": true,
  "conflict": null
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `canonical` | 是 | 统一后的写法 |
| `lang` | 是 | `en` / `zh` |
| `variants` | 是 | 原文出现过的其他写法（可为空数组） |
| `occurrences` | 是 | 至少一条，含原文写法与位置 |
| `first_occurrence` | 是 | 首现位置 |
| `abbreviation` | 否 | 缩写项填写；`defined_at` 为 null 表示原文未定义（不得编造全称） |
| `unified` | 是 | 本次是否已统一为 `canonical` |
| `conflict` | 否 | 存在冲突时写清冲突对象与多数派依据 |

## 与 edits 的联动

任何 `type` 含 `terminology` 的 edit，其 `reason` 必须引用本表条目，且该条目的 `occurrences` 必须包含该 edit 的 `location`。脚本不检查这一致性（留给自查清单），但评审会核。
