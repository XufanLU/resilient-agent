from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from .swe_checkpoint_workflow import Execution, Journal, SDKInvoker, load_task, run_experiment
from multiagent_debug_flow.state import InjectedDebugInterruption
from multiagent_debug_flow.usage_tracking import empty_token_usage

TASK = "sympy__sympy-24909"


def fake_factory(calls, *, reject=False):
    def factory():
        instance = object()
        async def invoke(kind, prompt):
            calls.append((instance, kind, prompt))
            if kind == "draft":
                output = {"diagnosis": "A deterministic test diagnosis", "plan": "A concrete plan " + str(len(calls))}
            elif kind == "critique":
                output = {"feedback": ["Preserve multiplication order and add regression checks."]}
            else:
                output = {"approved": not reject, "feedback": ["Address the missing regression case."] if reject else [],
                          "rationale": "Test reviewer verdict."}
            return output, {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10, "requests": 1}, {"response_ids": [f"fake-{len(calls)}"]}
        return invoke
    return factory


def metrics():
    return dict(token_usage=empty_token_usage(), agent_runs=0, initial_drafts=0, revisions=0,
                artifact_writes=0, checkpoint_writes=0, checkpoint_loads=0, checkpoint_bytes_written=0)


def test_pair_reloads_disk_state_and_passes_actual_feedback(tmp_path):
    calls = []
    summary = asyncio.run(run_experiment(TASK, tmp_path, "fake-test-only", invoker_factory=fake_factory(calls)))
    directory = Path(summary["result_directory"])
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    assert len({id(call[0]) for call in calls}) == 4  # new invoker before/after each interruption
    for arm, expected_calls in [("A", 6), ("B", 4)]:
        result = summary["arms"][arm]
        assert result["approved"] is True
        assert result["metrics"]["agent_runs"] == expected_calls
        outputs = [e for e in events if e.get("arm") == arm and e["event"] == "agent_output"]
        assert sum(e["token_usage"]["total_tokens"] for e in outputs) == result["metrics"]["token_usage"]["total_tokens"]
        assert result["metrics"]["pre_interruption_token_usage"]["total_tokens"] == 20
        assert result["metrics"]["recovery_token_usage"]["total_tokens"] == (expected_calls - 2) * 10
    assert summary["arms"]["A"]["metrics"]["checkpoint_loads"] == 0
    assert summary["arms"]["B"]["metrics"]["checkpoint_loads"] == 1
    assert len([e for e in events if e["event"] == "restart_state_cleared"]) == 1
    saved = json.loads((directory / "B" / "interruption_checkpoint.json").read_text())
    loaded = next(e for e in events if e["event"] == "checkpoint_loaded")
    interrupted = next(e for e in events if e.get("arm") == "B" and e["event"] == "interruption_raised")
    assert loaded["checkpoint_sha256"] == interrupted["checkpoint_sha256"]
    revision = next(e for e in events if e.get("arm") == "B" and e["event"] == "agent_input" and e["stage"] == "review_feedback_received")
    assert revision["prompt"]["saved_plan"] == saved["plan"]
    assert revision["prompt"]["reviewer_feedback"] == saved["reviewer_feedback"]
    assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))


@pytest.mark.parametrize("damage", ["plan", "feedback", "checkpoint", "task"])
def test_resume_rejects_missing_or_mismatched_state(tmp_path, damage):
    calls = []
    task = load_task(TASK)
    journal = Journal(tmp_path / "events.jsonl", "test")
    directory = tmp_path / "B"
    observed = metrics()
    factory = fake_factory(calls)
    with pytest.raises(InjectedDebugInterruption):
        asyncio.run(Execution(task, directory, "B", journal, observed, factory()).run(resume=False, allow_interrupt=True))
    if damage == "plan":
        (directory / "workspace" / "plan_v1.md").write_text("tampered")
    elif damage == "feedback":
        (directory / "workspace" / "feedback.json").write_text("[]")
    elif damage == "checkpoint":
        (directory / "checkpoint.json").unlink()
    else:
        task = {**task, "problem_statement": "Changed input"}
    with pytest.raises((ValueError, FileNotFoundError)):
        asyncio.run(Execution(task, directory, "B", journal, observed, factory()).run(resume=True, allow_interrupt=False))
    assert len(calls) == 2  # invalid state is rejected before another model call


def test_reviewer_rejection_is_not_reported_as_success(tmp_path):
    calls = []
    with pytest.raises(RuntimeError, match="bounded revision"):
        asyncio.run(run_experiment(TASK, tmp_path, "fake-test-only", invoker_factory=fake_factory(calls, reject=True)))
    assert not list(tmp_path.glob("*/summary.json"))
    failure = json.loads(next(tmp_path.glob("*/failure.json")).read_text())
    assert failure["completed_arms"] == []
    state = json.loads(next(tmp_path.glob("*/A/checkpoint.json")).read_text())
    assert state["approved"] is False


def test_real_agent_schemas_and_gold_patch_exclusion():
    invoker = SDKInvoker("gpt-5.4")  # construct only, no API calls
    assert set(invoker.agents) == {"draft", "critique", "review"}
    task = load_task(TASK)
    assert "patch" not in task and "test_patch" not in task


def test_sdk_usage_details_are_json_serializable(monkeypatch):
    from types import SimpleNamespace
    from agents import Runner
    from agents.usage import Usage
    from openai.types.responses.response_usage import InputTokensDetails, OutputTokensDetails

    async def fake_run(*args, **kwargs):
        return SimpleNamespace(
            final_output=SimpleNamespace(model_dump=lambda: {"diagnosis": "test", "plan": "test"}),
            context_wrapper=SimpleNamespace(usage=Usage(requests=1, input_tokens=12,
                output_tokens=8, total_tokens=20,
                input_tokens_details=InputTokensDetails(cached_tokens=4),
                output_tokens_details=OutputTokensDetails(reasoning_tokens=2))),
            raw_responses=[SimpleNamespace(response_id="test-response")])

    monkeypatch.setattr(Runner, "run", fake_run)
    output, usage, details = asyncio.run(SDKInvoker("gpt-5.4")("draft", {}))
    assert json.loads(json.dumps(details))["sdk_usage"]["input_tokens_details"]["cached_tokens"] == 4
    assert usage["total_tokens"] == 20
