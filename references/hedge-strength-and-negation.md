# 限定强度与否定范围（守恒判定依据）

本文件是“没改坏”的唯一判定依据。校验脚本 `scripts/check_minimal_edit.py` 的 `hedge-strength-changed` 与 `negation-scope-changed` 直接按本表执行；改动本表即全局生效，需同步跑一次回归。

## 1. 强度等级

| 等级 | 中文典型词 | English markers | 使用场景 |
|---|---|---|---|
| 5 强断言 | 证明、证实、确认、必然、总是、毫无疑问 | prove(s/d), demonstrate(s/d), confirm(s/ed), establish(es/ed), always, necessarily, definitely, conclusively, undoubtedly | 重复实验后的确定结论 |
| 4 较强 | 表明、显著、强烈、支持（有数据时） | show(s/n), indicate(s/d), significantly, strongly, clearly, support(s) | 主结果、统计显著 |
| 3 中等 | 提示、相关于、与……相关、一致于、暗示 | suggest(s/ed), associated with, correlated with, correlates with, related to, consistent with, implies | 观察性研究、机制推测 |
| 2 较弱 | 可能、或许、似乎、推测、倾向于、可能 | may, might, could, can, appear(s), seem(s), possibly, presumably, likely, tends to | 探索性发现、小样本 |
| 1 最弱 | 尚不清楚、尚不明确、有待进一步、初步、证据有限 | remains unclear, is unknown, warrants further, preliminary, limited evidence, has yet to | 研究空白、未来工作 |

判定方法：句子命中的**最高等级**即该句的主张强度。改后最高等级必须与改前相同。

## 2. 禁止的升降格

| 原等级 | 改后 | 是否允许 | 处理 |
|---|---|---|---|
| 2（may） | 5（proves） | 禁止 | 回退改写，或把改写点写进 `uncertainty` 交作者确认 |
| 3（associated with） | 5/4（causes / leads to） | 禁止 | 相关性不得升格为因果，必须回退 |
| 5（demonstrates） | 2（may indicate） | 禁止 | 削弱结论同样违规 |
| 4（significantly） | 单去掉 “significantly” | 禁止 | 显著性标记属数据性表述，不可删 |
| 同级互换（may → might） | 2 → 2 | 允许 | 但需在 `reason` 说明理由 |

例外：作者**明确要求**降低或提高语气时，才可改；此时在 `edits[].reason` 写明“按作者要求调整强度，原文 X → 改文 Y”，并在 `uncertainty` 留痕。

## 3. 否定范围

必须原样保留的否定/限定结构：

- 否定词：`not / no / never / none / neither / nor / without / cannot / fails to / 不 / 未 / 无 / 非 / 没有 / 不能 / 无法`
- 限定范围：`only / except / excluding / unless / 仅 / 只 / 除非`
- 条件句：`only if / unless / under / when / provided that / 若 / 仅当 / 除非`
- 量词：`all / most / some / many / few / none / 全部 / 多数 / 部分 / 少数`

**位置**同样重要：`Only A inhibits B` 不能改成 `A inhibits B only`（后者可能被读成“只抑制不其他”）。

## 4. 相关性与因果性

| 原文写法（弱） | 禁止改成（强） |
|---|---|
| associated with | causes / leads to / results in / drives / determines |
| correlated with | is responsible for |
| related to | due to |
| suggests | proves / demonstrates |
| consistent with | confirms |

反向（因果降级为相关）同样是违规，会让作者主张被削弱。校验脚本对两个方向都报错（`causal-escalation` / `causal-weakening`）。
