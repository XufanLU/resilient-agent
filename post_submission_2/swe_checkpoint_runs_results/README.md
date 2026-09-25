# SWE checkpoint sample — 25 September 2026

All 12 selected tasks have now completed under this protocol. See the
[complete batch report](batch_report.md) and [combined raw results](combined_results.jsonl).
The first two samples are detailed below; the remaining ten were run by
`post_submission_2/run_remaining_metadata.py`.

Completed one live A/B pair for `sympy__sympy-24909` (the `milli*W` issue), using
`gpt-5.4` configured in the local `.env`. Credentials are not copied to results.

| Measured quantity | A: restart | B: disk resume | B − A |
| --- | ---: | ---: | ---: |
| Total wall time (s) | 47.055 | 26.137 | −20.918 |
| Tokens before interruption (through saved feedback checkpoint) | 2,153 | 2,112 | −41 |
| Tokens after restart/resume | 6,281 | 3,497 | −2,784 |
| Combined total tokens | 8,434 | 5,609 | −2,825 |
| Agent calls | 6 | 4 | −2 |
| Recovery wall time (s) | 30.721 | 10.001 | −20.720 |
| Disk checkpoint loads | 0 | 1 | +1 |

Totals include work before interruption and work after recovery. Both arms'
final plans were approved by the model reviewer on the first revision. API
usage reported zero cached input tokens for this pair. The totals exclude the
incomplete first attempt described below; they are not total account spend.

For B, the combined total is **2,112 + 3,497 = 5,609 tokens**. The 2,112
tokens before interruption comprise 1,181 input and 931 output tokens from
the initial draft and critique. The 3,497 tokens after resume comprise 2,633
input and 864 output tokens from revision and final review. The original
reported total of 5,609 already included both phases; adding 2,112 to that
total again would double-count the initial work. Saving/loading the local
checkpoint itself makes no model call. Saved plan and feedback sent to the
model during revision are included in the post-resume input-token count.

## Evidence

These files were relocated into `post_submission_2`. Recorded absolute paths
inside raw run JSON/JSONL still refer to their original location; use the links
below for their current location. Execution-time source hashes are preserved.

The complete successful run is in
[`swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d`](swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d/):

- [Summary and per-arm measurements](swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d/summary.json)
- [All 48 events, prompts, outputs, response IDs and usage](swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d/events.jsonl)
- [Independent reconciliation results](swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d/verification.json)
- [B's saved interruption checkpoint](swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d/B/interruption_checkpoint.json)
- [B's revised plan](swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d/B/workspace/plan_v2.md)
- [Configuration, versions, and source/input hashes](swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d/manifest.json)

The verifier checks event continuity, input/output pairing, every token total,
identical task metadata, interruption and load hashes, delivery of B's saved
plan/diagnosis/feedback to revision, final artifact hashes, and summary deltas.
It passed. Fourteen offline tests also passed across the SWE adaptation,
existing synthetic workflow, and recovery middleware.

```bash
python3 post_submission_2/swe_checkpoint_runs/verify_sample.py \
  post_submission_2/swe_checkpoint_runs/swe_checkpoint_sympy__sympy-24909_20260925T113810Z_2fd9d23d
```

## What this sample establishes

This is a new protocol, separate from the historical scripted SWE runs. It
raises a real exception after persisting an initial model critique, then
creates new execution/agent objects. A discards its checkpoint and workspace;
B reads its checkpoint from disk and validates workspace consistency before
continuing. Thus, the observed six versus four calls result from the executed
restart/resume paths. The first critique is mandatory by protocol, so avoiding
two repeated initial calls is an expected accounting result. Final approval
is a model decision and additional revisions can change the total call counts.

This is **metadata planning**, not a full SWE-bench repair evaluation. No source
repository was checked out, no source patch applied, and no SWE tests executed.
Model approval is approval of a plan only. The interruption is a Python
exception within one process, not an external process kill. Both arms write
checkpoints before interruption, so this does not measure checkpoint overhead
against a baseline with no checkpoint writes.

Task inputs and fault location match; initial model plans/feedback are generated
independently. There is no shared response cache or controlled API caching,
no fixed generation seed, and no temperature setting. A ran before B. Remote
API latency, generated output length, and runtime variation remain uncontrolled.
One pair cannot support significance claims, timing independence claims, or
general speedup estimates. Historical summaries and detailed logs were unchanged.

## Preserved incomplete attempt

[The first attempt](swe_checkpoint_sympy__sympy-24909_20260925T113526Z_f24af5d1/README.md)
received one model response but failed to serialize nested SDK usage details.
Its response and token count were not saved, so its spend is unknown from the
local artifacts. It remains separate and is excluded from the completed pair.
The serialization bug was fixed and covered by a regression test before retry.

## Run another sample

The sample used the isolated environment
`/private/tmp/resilient-agent-debug-rerun-venv` with `openai==2.7.1`,
`openai-agents==0.4.2`, `python-dotenv==1.1.1`, and `pydantic==2.13.5`.

```bash
/private/tmp/resilient-agent-debug-rerun-venv/bin/python \
  -m multiagent_debug_flow.workflow \
  --swe-task-id sympy__sympy-24909 \
  --root post_submission_2/swe_checkpoint_runs --env-file .env
```

Each invocation makes paid API calls and creates a new directory. See
[`multiagent_debug_flow/README.md`](../../multiagent_debug_flow/README.md)
for the protocol and CLI documentation.

## Second sample: django__django-13447

Completed on 25 September 2026 using the same GPT-5.4 metadata planning and
checkpoint protocol. This issue concerns model-class access in Django admin's
`app_list` context. A ran before B, with one injected interruption per arm.

| Measured quantity | A: restart | B: disk resume |
| --- | ---: | ---: |
| Tokens before interruption | 2,130 | 2,219 |
| Tokens after restart/resume | 5,951 | 4,235 |
| Combined total tokens | 8,081 | 6,454 |
| Agent calls | 6 | 4 |
| Total wall time (s) | 42.198 | 31.703 |

B's total includes both phases: **2,219 + 4,235 = 6,454 tokens**. Its observed
total is 1,627 tokens and 10.495 seconds lower than A. Both final plans were
approved by the model reviewer. All 48 events reconcile with the summaries;
B loaded exactly one disk checkpoint and used the saved plan and feedback.
Reported cached input tokens were zero for both arms. No attempt failed for
this task. No repository patch or SWE tests were executed; the same scope and
methodological limits described for the first sample apply.

- [Summary](swe_checkpoint_django__django-13447_20260925T115357Z_2dd0cb10/summary.json)
- [Complete call and recovery logs](swe_checkpoint_django__django-13447_20260925T115357Z_2dd0cb10/events.jsonl)
- [Passed verification](swe_checkpoint_django__django-13447_20260925T115357Z_2dd0cb10/verification.json)
- [Saved interruption checkpoint for B](swe_checkpoint_django__django-13447_20260925T115357Z_2dd0cb10/B/interruption_checkpoint.json)
