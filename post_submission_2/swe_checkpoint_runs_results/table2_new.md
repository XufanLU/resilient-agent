# Table II — new metadata-planning checkpoint results

Twelve paired tasks; differences are B (checkpoint resume) minus A (restart). Negative values indicate lower measured usage/time for B.

| Metric | Mean Δ (B − A) | 95% Student-t CI |
| --- | ---: | --- |
| Wall-clock time (s) | -15.54 | [-18.05, -13.03] |
| Total tokens | -4648.33 | [-6583.15, -2713.52] |
| Agent runs | -2.00 | — (constant count) |
| Repeated initial diagnoses/plans (derived) | -1.00 | — (constant count) |

Agent-run differences are exactly −2 in all 12 pairs (observed range [−2, −2]). Repeated initial diagnosis/plan differences are exactly −1 (observed range [−1, −1]). These are accounting results, not estimated statistical uncertainty.

Repeated initial diagnoses/plans are derived from `max(initial_drafts - 1, 0)` and verified against initial draft outputs containing a diagnosis. A has two initial drafts and B one. This is not a separately instrumented repository-diagnosis metric; use the explicit label above when reporting the new protocol.

Total tokens include input and output tokens before interruption and after restart/resume. Wall time includes both phases and persistence/logging overhead. The previously shown Table II intervals match the old script's 1.96 normal fallback; these results require SciPy and use Student t (df=11). Normal-approximation values and raw paired observations are retained in `table2_new.json` for comparison.

The confidence intervals assume independent pair differences. Fixed A-before-B order, API/runtime variability, and independently generated plans limit causal interpretation. These experiments evaluate metadata planning and disk state recovery, not executable software repair. Counts do not support general efficiency claims.

Reproduce: `python3 -m post_submission_2.calculate_table2` (SciPy required).

Source: [12 new pairs](combined_results.jsonl). [Exact calculations and paired values](table2_new.json).
