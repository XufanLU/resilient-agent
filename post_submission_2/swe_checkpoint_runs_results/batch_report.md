# All 12 SWE metadata checkpoint pairs

Completed on 25 September 2026. The batch added 10 verified pairs to the two earlier samples, with no failed attempts in this batch.

All 576 events reconcile with their per-arm summaries. Every task has exactly one completed pair, both plans approved, and one verified disk checkpoint load in B.

[Combined raw results (one pair per line)](combined_results.jsonl) · [Batch status](batch_status.json)

## Tokens: before interruption + after recovery = total

Both input and output tokens are included. A repeats work after discarding state; B resumes from persisted plan and reviewer feedback.

| Task | A before | A after | A total | B before | B after | B total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [django__django-11905](swe_checkpoint_django__django-11905_20260925T120714Z_cfedbdac/summary.json) | 2,990 | 7,692 | 10,682 | 3,416 | 5,179 | 8,595 |
| [django__django-13447](swe_checkpoint_django__django-13447_20260925T115357Z_2dd0cb10/summary.json) | 2,130 | 5,951 | 8,081 | 2,219 | 4,235 | 6,454 |
| [django__django-16041](swe_checkpoint_django__django-16041_20260925T120834Z_fed80f27/summary.json) | 6,553 | 14,034 | 20,587 | 6,166 | 7,457 | 13,623 |
| [matplotlib__matplotlib-18869](swe_checkpoint_matplotlib__matplotlib-18869_20260925T120928Z_31d14dfe/summary.json) | 3,897 | 8,399 | 12,296 | 3,446 | 5,342 | 8,788 |
| [matplotlib__matplotlib-23299](swe_checkpoint_matplotlib__matplotlib-23299_20260925T121043Z_3e3e4f3b/summary.json) | 12,400 | 27,302 | 39,702 | 12,552 | 14,782 | 27,334 |
| [mwaskom__seaborn-3407](swe_checkpoint_mwaskom__seaborn-3407_20260925T121207Z_05e9016f/summary.json) | 7,622 | 17,315 | 24,937 | 7,749 | 9,469 | 17,218 |
| [pytest-dev__pytest-8365](swe_checkpoint_pytest-dev__pytest-8365_20260925T121319Z_42bbe44d/summary.json) | 4,100 | 9,171 | 13,271 | 3,853 | 5,291 | 9,144 |
| [scikit-learn__scikit-learn-13241](swe_checkpoint_scikit-learn__scikit-learn-13241_20260925T121424Z_0d51673d/summary.json) | 4,630 | 10,472 | 15,102 | 4,405 | 5,950 | 10,355 |
| [scikit-learn__scikit-learn-15512](swe_checkpoint_scikit-learn__scikit-learn-15512_20260925T121538Z_df30d49a/summary.json) | 3,544 | 8,951 | 12,495 | 3,598 | 5,543 | 9,141 |
| [sympy__sympy-16503](swe_checkpoint_sympy__sympy-16503_20260925T121645Z_fc870f38/summary.json) | 3,955 | 8,706 | 12,661 | 3,588 | 5,037 | 8,625 |
| [sympy__sympy-21055](swe_checkpoint_sympy__sympy-21055_20260925T121748Z_03484dea/summary.json) | 2,763 | 7,566 | 10,329 | 2,983 | 4,928 | 7,911 |
| [sympy__sympy-24909](swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d/summary.json) | 2,153 | 6,281 | 8,434 | 2,112 | 3,497 | 5,609 |
| **All 12** | **56,737** | **131,840** | **188,577** | **56,087** | **76,710** | **132,797** |

## End-to-end time and agent calls

Times include initial work, interruption, restart/resume, persistence, and local event logging.

| Task | A seconds | B seconds | A calls | B calls |
| --- | ---: | ---: | ---: | ---: |
| django__django-11905 | 46.287 | 34.031 | 6 | 4 |
| django__django-13447 | 42.198 | 31.703 | 6 | 4 |
| django__django-16041 | 34.980 | 19.568 | 6 | 4 |
| matplotlib__matplotlib-18869 | 46.449 | 28.049 | 6 | 4 |
| matplotlib__matplotlib-23299 | 51.889 | 32.357 | 6 | 4 |
| mwaskom__seaborn-3407 | 42.365 | 28.939 | 6 | 4 |
| pytest-dev__pytest-8365 | 42.416 | 23.373 | 6 | 4 |
| scikit-learn__scikit-learn-13241 | 46.594 | 26.781 | 6 | 4 |
| scikit-learn__scikit-learn-15512 | 40.125 | 27.186 | 6 | 4 |
| sympy__sympy-16503 | 39.061 | 24.018 | 6 | 4 |
| sympy__sympy-21055 | 44.689 | 35.492 | 6 | 4 |
| sympy__sympy-24909 | 47.055 | 26.137 | 6 | 4 |

## Scope and provenance

These are metadata-planning experiments with actual API calls, injected exceptions, and disk checkpoint recovery. They do not edit repository source or execute SWE repository tests. The separate Django repository check is not included in these measurements.

All pairs used GPT-5.4, A-before-B order, the same selected input metadata per pair, and the same interruption boundary. Initial plans and critiques were independently generated. Remote latency, output length, and prompt caching are not controlled; these observations do not establish independent timing samples or isolate a general policy effect.

The six-versus-four call pattern is an accounting consequence of avoiding the initial draft and critique after recovery when one revision suffices. Final reviewer approval was model-generated. The original two samples ran earlier than this batch; the first sample also predates the source-file relocation. Each run manifest records its actual configuration and source hash.

The combined file preserves the raw summaries, including execution-time absolute paths. The task links above point to current locations. Original historical 12-task results are not mixed into this file. The incomplete first-ever sample attempt is excluded; its unrecorded usage is not represented in these totals.

Each task directory includes `events.jsonl`, `summary.json`, `verification.json`, configuration, input metadata, and per-arm checkpoint/workspace files. No failed pair was silently replaced in this batch.

To check a run: `python3 post_submission_2/swe_checkpoint_runs/verify_sample.py RUN_DIRECTORY`.
To run only remaining selected tasks: `python -m post_submission_2.run_remaining_metadata` (paid API calls only for missing pairs).
