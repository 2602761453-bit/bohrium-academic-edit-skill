# academic-edit-minimal

Minimal-edit academic language polishing skill — polish academic text **without changing the author's claims**.

It is built for one failure mode that polished text usually introduces: the edit silently strengthens or weakens hedging, changes numbers or units, or shifts citation and figure pointers. This skill edits only what is wrong or inconsistent, logs every sentence, and enforces three conservation guards with a deterministic checker.

## What it guarantees

| Guard | What it checks |
|---|---|
| Hedging and negation | Strength level of the sentence is unchanged (`may` never becomes `demonstrates`); negation scope, conditions and quantifiers preserved; correlation is never upgraded to causation |
| Numbers and units | Numeric values, units, `p` values, sample sizes and percentages unchanged; hyphenated identifiers such as `FEV-1` are not mistaken for numbers |
| Citations and figure pointers | `[12]`, `[3-5]`, `(Smith, 2020)`, `Fig. 2`, `Table 1`, `§2.1` keep their numbers |

## Contents

```text
SKILL.md                              # entry point: trigger conditions, 5-step workflow, output contract
scripts/check_minimal_edit.py         # guards + output-contract check (stdlib only, offline)
references/
  hedge-strength-and-negation.md      # strength levels, forbidden upgrades, negation scope
  edit-type-labels.md                 # change-type vocabulary and reason format
  terminology-template.md             # terminology table fields
  style-rules.md                      # minimal-edit principles, protected objects, register quick reference
使用与方法说明.md                       # full Chinese usage guide (deps, steps, fields, failures, self-check)
```

## Output contract

Each case produces one JSON result with `case_id`, `status` (`success` / `partial` / `insufficient_material`), `polished_text`, a sentence-by-sentence `edits` list (original / revised / type / reason / guards), a `terminology` table, an `evidence` map (numbers, citations, figures with source locations), `uncertainty` notes, and `contract_map` covering every key named by the input `output_contract`.

## Usage

```bash
python3 scripts/check_minimal_edit.py --case case.json --result result.json
```

Exit codes: `0` pass, `2` conservation violation, `3` contract/field problem, `4` unreadable input. A non-zero exit means the result must not be reported as complete.

## Limits

- Text inputs only; scanned PDFs need an OCR text layer first.
- No scientific judgement: it never rewrites conclusions, only language.
- Long documents are processed section by section; cross-section consistency covers terminology and claim strength, not paragraph rewrites.

## Related

Built for the Bohrium Playground skill challenge `product-arena-02-7051d92d` (写作02 | 学术语言润色), direction: minimum-edit / meaning-preservation.
