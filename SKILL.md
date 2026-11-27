---
name: academic-edit-minimal
description: Minimal-edit academic language polishing that preserves meaning, evidence and hedging. Use when a user hands over an academic manuscript, abstract, thesis section, grant text or bilingual draft and asks for polishing, proofreading, revision, register adjustment or terminology unification, and the result must be a full revised text plus a sentence-by-sentence change log. It edits only what is wrong or inconsistent, keeps hedging strength, numbers, units, citation numbers and figure or table pointers unchanged, emits a terminology table and an evidence map, and refuses to invent facts. Do not use it for pure content questions, full translation as the only goal, or inventing results.
---

# 学术语言润色（最小编辑 / 语义保持）

本 Skill 的目标不是“把文字写得漂亮”，而是**在不改作者主张的前提下**把学术文本改对。核心纪律三条：**最小编辑**（只改错的地方）、**逐句留痕**（每处改动可复核）、**守恒**（限定强度、数值单位、引用编号、图表指向一字不动）。

## 1. 触发条件

满足任意一条即应使用：

- 用户给出**整段/整篇/整节**学术文本，要求润色、改写、校对、审修、润饰、语言打磨；
- 要求**统一术语**、统一缩写首现、统一大小写与连字符；
- 要求调整**文体与语域**（期刊论文 / 学位论文 / 基金申请 / 审稿回复 / 英文摘要）；
- 输入是案例目录，包含 `case.json`（含 `case_id`、正文、`output_contract`）与 `task.md`。

**不应使用**（触发就要拒绝或改问）：

- 纯内容问答、“这段讲了什么”；
- 只需要翻译、不要求保留原文结构的整篇翻译；
- 要求补造数据、补写实验结果、把“可能”写成“证明”；
- 输入里没有任何可编辑正文。

## 2. 输入与输出

### 输入

| 来源 | 必需 | 说明 |
|---|---|---|
| `case.json` 的 `case_id` | 是 | 原样回填到输出 |
| `case.json` 的 `output_contract` | 是 | **该案例要求的输出键名，逐个都要满足** |
| 待润色正文 | 是 | 字段名不固定：`text` / `manuscript` / `source_text` / 随附 `.md` `.txt` `.tex` 文件 |
| `target_style` / `register` | 否 | 缺省按“期刊论文”处理，并在输出记为 `unknown` |
| `terminology` | 否 | 预置术语表，形如 `{"规范写法": ["变体1", "变体2"]}` |
| `task.md` | 否 | 人读的任务说明，优先于缺省假设 |

正文不在 `case.json` 里时，按 `/input/` 下的文件寻找；**必须读真实文件，不能凭字段名猜内容**。

### 输出：`/app/output/result.json`

固定骨架（字段含义见第 5 节）：

```json
{
  "case_id": "<原样回填>",
  "status": "success | partial | insufficient_material",
  "status_reason": "<partial / insufficient_material 时必填>",
  "register": "journal | thesis | grant | referee_response | abstract | unknown",
  "language": "en | zh | bilingual",
  "polished_text": "<润色后全文>",
  "edits": [],
  "terminology": [],
  "evidence": {"numbers": [], "citations": [], "figures": []},
  "uncertainty": [],
  "contract_map": {"<output_contract 的键>": "<本结果中对应字段的取值或指针>"}
}
```

**硬性要求**：`output_contract` 里出现的每一个键，都必须在 `result.json` 顶层存在（值可由本骨架字段映射而来，用 `contract_map` 说明对应关系）。键名每个案例不同，**禁止硬编码**——先读契约，再决定写什么。

## 3. 处理流程（五步，不可跳步）

### 第 0 步：读契约与正文

1. 读 `case.json`，列出 `output_contract` 的全部键与值说明，抄进工作笔记。
2. 读正文；记录体裁、语訃�Z�向、输入形态（纯文本 / Markdown / LaTeX / 混排）。
3. 标出**保护对象**：公式块、引用编号、图表编号、数值与单位、参考文献块。

### 第 1 步：冻结术语表

抽取领域术语、缩写与全称、大小写与连字符写法、疑似同义混用。冲突时以**原文多数用法**为准，把少数派记进 `uncertainty`。术语表在本步一次性冻结，后续所有改动只能引用它。

### 第 2 步：逐句最小编辑

**逐句**处理，不是逐段重写。对每一句：

- 没有硬错误 → 原样保留，记为 `no-change`（**必须入清单**，否则无法证明“没改坏”）；
- 有硬错误 → 只改错误处，其余措辞与信息结构保留；
- 修改类型只能取第 5 节标签表中的一个或多个。

**禁止**：为“更地道”整体重写；把被动改主动、名词化改动词化当作错误；扩写成更强的结论；删掉限定词让句子更利落。

### 第 3 步：守恒检查（每句被改过的都要做）

按 [references/hedge-strength-and-negation.md](references/hedge-strength-and-negation.md) 判定原文主张的强度等级与否定范围，确认改后**未越级、未削弱、未改变否定范围与条件**。同时核对：

- 数值、单位、`p` 值、样本量：一字不改；
- 引用编号 `[12]` `[3-5]` `(Smith, 2020)`：编号与作者年份都对得上；
- 图表指向 `Fig. 2` `Table 1` `图 3` `表 2`：编号不变；
- 相关性不得升格为因果（`associated with` ≠ `causes`）。

### 第 4 步：机器校验

```bash
python3 scripts/check_minimal_edit.py --case /input/case.json --result /app/output/result.json
```

退出码 `0` 通过；`2` 守恒违规；`3` 契约或字段缺失；`4` 输入不可读。**退出码非 0 不得宣称完成**：能修就修后重跑，修不动就降级为 `partial` 并把违规写进 `uncertainty`。

### 第 5 步：按契约产出

先写 `status`，再写结果。`contract_map` 逐个键声明映射；契约里有、骨架里没有的键，必须显式给出对应值，不能省略。

## 4. 逐句修改清单字段

每条 `edits[]` 必须含全部字段：

| 字段 | 要求 |
|---|---|
| `sent_id` | 稳定编号，如 `s12` |
| `location` | 可定位，如 `§3 ¶2 s4` |
| `original` | **完整原句**，不得截断或只写片段 |
| `revised` | 改后整句；`no-change` 时与 `original` 相同 |
| `type` | 见第 5 节标签，可多选 |
| `reason` | 一句话说明为什么改；数值/单位/引用被格式化改动时须写明“仅格式，未改数值” |
| `guards` | 本句守恒结论：`numbers_ok`、`citations_ok`、`figures_ok`、`hedge_ok`、`negation_ok` 五个布尔 |

**覆盖要求**：`edits` 必须覆盖全文每一句，包括没改的句子。

## 5. 修改类型标签

| 标签 | 含义 | 典型场景 |
|---|---|---|
| `grammar` | 语法/句法硬错误 | 主谓一致、时态、冠词、介词、单复数、悬垂修饰 |
| `usage` | 用词/搭配不当 | 中式搭配、错误介词、词义误用 |
| `register` | 语域/语气不合体裁 | 口语化、宣传化、绝对化、人称误用 |
| `terminology` | 术语不统一 | 同一概念多种写法、缩写首现未展开、大小写/连字符漂移 |
| `clarity` | 冗余或长句造成理解成本 | 冗余连接词、重复、超长句切分 |
| `format` | 标点、空格、编号格式 | 多余空格、全角半角、标点重复 |
| `no-change` | 该句无需修改 | 保留原句，用于证明全覆盖 |

标签表与判定细则见 [references/edit-type-labels.md](references/edit-type-labels.md)；风格规则见 [references/style-rules.md](references/style-rules.md)；术语表字段见 [references/terminology-template.md](references/terminology-template.md)。

## 6. 异常处理

| 情况 | 处置 |
|---|---|
| **术语表冲突**（预置表内部或与原文多数用法冲突） | 以原文多数用法为准完成编辑，冲突项写进 `terminology[].conflict` 与 `uncertainty`，`status` 不因之降级，但不得静默二选一 |
| **材料不足**（只有摘要、缺方法、缺参考文献表） | 只处理可见部分，`status=insufficient_material`，`status_reason` 写明缺什么、影响哪些结论 |
| **文体不明** | 默认按期刊论文处理，`register=unknown`，`uncertainty` 提示可切换 |
| **编码混乱/乱码** | 不猜测改写；`status=insufficient_material`，定位乱码区段 |
| **公式与引用混排** | 公式块与引用标记原样保留，只处理外围叙述文字 |
| **输入超长** | 分段处理，每段独立 `edits`，`status_reason` 写明分段位置与未处理段 |
| **多次重复润色同一段** | 结论必须稳定；若两次结果不同，说明哪一版为准，并把差异写入 `uncertainty` |

## 7. 自查清单（交付前逐条过）

- [ ] `case_id` 与输入一致；`output_contract` 的键全部存在
- [ ] `edits` 覆盖全文每一句，`no-change` 也在其中
- [ ] 每条 `edits` 的 `guards` 五项全为真，或有明确例外说明
- [ ] 数值、单位、`p` 值、样本量、引用编号、图表编号与原文逐一对得上
- [ ] 限定强度等级未变；否定范围、条件句、量词未变；相关性未升格为因果
- [ ] 术语表已冻结且被实际引用；冲突项已记入 `uncertainty`
- [ ] `status` 与实际完成度一致，部分完成写清边界
- [ ] `scripts/check_minimal_edit.py` 退出码为 0

## 8. 适用范围与限制

- 只处理**有正文**的输入；扫描件需先取得文字层。
- 不做研究内容判断：句子科学上是否成立由作者负责，本 Skill 不改结论。
- 不负责翻译质量本身，只负责“保留原意前提下的语言质量”。
- 长文档（>15000 词）以分段方式处理，跨段一致性只能保证术语与主张强度，不保证段落衔接重写。
