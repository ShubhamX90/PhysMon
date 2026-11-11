# G0 (b): formula-hint record (Phase I, five stable families)

Data role EXPLORATION; audit of committed Phase-I records. `S_lp shift` = L(base) - L(hint) of the bare certified string, so a positive value means the correct formula hint LOWERED the gold-string log-probability and the legacy label fires at >= 0.5.

| Model | Family | S_lp shift | Answer (base) | Answer (hint) | Gold | Transition (1e-3) | (1e-2) |
|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-7B-Instruct | CM_A_STD_009_FORMULA | 3.688 | 12.0 Nm | 12.0 Nm | 12.0 N*m | stays_correct | stays_correct |
| Qwen/Qwen2.5-7B-Instruct | CM_B_010_FORMULA | 3.859 | 15.0 N*m | 15.0 N*m | 15.0 N*m | stays_correct | stays_correct |
| Qwen/Qwen2.5-7B-Instruct | CM_B_UM_028_FORMULA | 4.203 | 15.0 N*m | 15.0 N*m | 15.0 N*m | stays_correct | stays_correct |
| Qwen/Qwen2.5-7B-Instruct | TH_B_UM_001_FORMULA | 3.844 | 41860.0 J | 41860.0 J | 41860 J | stays_correct | stays_correct |
| Qwen/Qwen2.5-7B-Instruct | TH_B_UM_003_FORMULA | 5.531 | 10460 J | 41860.0 J | 41860 J | becomes_correct | becomes_correct |
| meta-llama/Llama-3.1-8B-Instruct | all | NOT_EVALUATED: no records with this model_name in prompt_records.jsonl; results/appendix/formula_leakage/behavioural/llama_primary_formula_stub.jsonl holds only ['Qwen/Qwen2.5-7B-Instruct'] and is byte-identical to ['results/appendix/formula_leakage/behavioural/qwen_primary_20260620T063936Z.jsonl', 'results/appendix/formula_leakage/behavioural/qwen_primary_20260620T074602Z.jsonl', 'results/appendix/formula_leakage/behavioural/qwen_primary_20260620T084819Z.jsonl'] | | | | | |

Grading rule: first number within relative tolerance of the certified value and unit equal after removing spaces, '*', '·', '⋅'; chosen after seeing the answers (descriptive).
Identical run files: [['results/appendix/formula_leakage/behavioural/llama_primary_formula_stub.jsonl', 'results/appendix/formula_leakage/behavioural/qwen_primary_20260620T063936Z.jsonl', 'results/appendix/formula_leakage/behavioural/qwen_primary_20260620T074602Z.jsonl', 'results/appendix/formula_leakage/behavioural/qwen_primary_20260620T084819Z.jsonl']].
