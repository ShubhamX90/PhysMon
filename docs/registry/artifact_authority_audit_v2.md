# Artifact Authority Audit v2

- Artifacts scanned: 1764
- Experiments resolved: 6
- Experiments partially resolved: 1
- Critical unresolved: 4

| Experiment | Issue | Decision | Status | Criticality |
|---|---|---|---|---|
| stage12_llama_full_32head_sweep | partial_vs_full_summary | full_summary_authoritative_for_exploratory_use | resolved | noncritical |
| stage11_variable_renaming_probe_corrected | corrected_labels | corrected_summary_supersedes_original_if_both_present | partially_resolved | critical |
| stage10_deepseek_top4_mhk_qwen_panel | panel_mismatch | not_authoritative_for_clean_deepseek_causal_claim | resolved_for_boundary_claim | critical |
| stage12_qwen3b_incomplete_behavioural | incomplete_run | partial_not_reportable | unresolved | critical |
| stage12_donor_renamed_same_answer | control_completion_check | complete_exploratory_if_rows_present | resolved | noncritical |
| stage12_donor_renamed_stable | control_completion_check | complete_exploratory_if_rows_present | resolved | noncritical |
| stage13_nested_stage6_archive_audit | nested_archive_difference_unknown | critical_unresolved | unresolved | critical |
| stage13_stale_canonical_verification | stale_verification | v2_verification_authoritative_for_current_remediation | resolved | noncritical |
| appendix_formula_leakage | diagnostic_status | complete_exploratory_not_pending | resolved | noncritical |
| stage13_empty_placeholder_audit | empty_placeholder_outputs | placeholders_not_scientific_nulls | resolved | noncritical |
