"""Independently reconcile a completed SWE checkpoint sample's saved files.

Usage: python3 post_submission_2/swe_checkpoint_runs/verify_sample.py RUN_DIRECTORY
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory):
    summary = json.loads((directory / "summary.json").read_text())
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    task = json.loads((directory / "task.json").read_text())
    assert not (directory / "failure.json").exists()
    assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
    assert len({e["event_id"] for e in events}) == len(events)
    assert {e["experiment_id"] for e in events} == {summary["experiment_id"]}
    assert events[-1]["event"] == "experiment_completed"
    assert not any(e["event"] in ("agent_error", "experiment_failed") for e in events)
    assert json.loads((directory / "results.jsonl").read_text()) == summary
    checks = {}
    for arm in ("A", "B"):
        arm_events = [e for e in events if e.get("arm") == arm]
        counts = Counter(e["event"] for e in arm_events)
        inputs = {e["call_id"]: e for e in arm_events if e["event"] == "agent_input"}
        outputs = {e["call_id"]: e for e in arm_events if e["event"] == "agent_output"}
        assert inputs.keys() == outputs.keys()
        assert len(inputs) == counts["agent_input"] == counts["agent_output"]
        result = summary["arms"][arm]
        assert result == json.loads((directory / f"arm_{arm}.json").read_text())
        assert result == next(e["result"] for e in arm_events if e["event"] == "arm_completed")
        metrics = result["metrics"]
        assert len(inputs) == metrics["agent_runs"]
        for e in inputs.values():
            assert e["prompt"]["task"] == task
        for e in outputs.values():
            assert e["response_ids"] and all(e["response_ids"])
            assert e["token_usage"]["total_tokens"] == e["token_usage"]["input_tokens"] + e["token_usage"]["output_tokens"]
            assert e["duration_s"] > 0
        interrupted = next(e for e in arm_events if e["event"] == "interruption_raised")
        before = [e for e in outputs.values() if e["sequence"] < interrupted["sequence"]]
        after = [e for e in outputs.values() if e["sequence"] > interrupted["sequence"]]
        for key in ("input_tokens", "output_tokens", "total_tokens", "requests"):
            assert sum(e["token_usage"][key] for e in outputs.values()) == metrics["token_usage"][key]
            assert sum(e["token_usage"][key] for e in before) == metrics["pre_interruption_token_usage"][key]
            assert sum(e["token_usage"][key] for e in after) == metrics["recovery_token_usage"][key]
            assert all(e["sdk_usage"][key] == e["token_usage"][key] for e in outputs.values())
        assert counts["interruption_raised"] == counts["interruption_caught"] == 1
        assert counts["execution_started"] == 2
        assert counts["checkpoint_saved"] == metrics["checkpoint_writes"]
        assert counts["checkpoint_loaded"] == metrics["checkpoint_loads"] == (1 if arm == "B" else 0)
        snapshot_path = directory / arm / "interruption_checkpoint.json"
        assert sha256(snapshot_path) == interrupted["checkpoint_sha256"]
        snapshot = json.loads(snapshot_path.read_text())
        assert snapshot["stage"] == "review_feedback_received"
        assert snapshot["next_action"] == "revise_plan" and snapshot["plan_version"] == 1
        if arm == "B":
            loaded = next(e for e in arm_events if e["event"] == "checkpoint_loaded")
            assert loaded["checkpoint_sha256"] == interrupted["checkpoint_sha256"]
            revision = min((e for e in inputs.values() if e["sequence"] > loaded["sequence"]), key=lambda e: e["sequence"])
            assert revision["prompt"]["saved_plan"] == snapshot["plan"]
            assert revision["prompt"]["saved_diagnosis"] == snapshot["diagnosis"]
            assert revision["prompt"]["reviewer_feedback"] == snapshot["reviewer_feedback"]
            assert counts["restart_state_cleared"] == 0
        else:
            assert counts["restart_state_cleared"] == 1
            assert next(e for e in arm_events if e["event"] == "restart_state_cleared")["workspace_exists"] is False
        checkpoint_path = directory / arm / "checkpoint.json"
        state = json.loads(checkpoint_path.read_text())
        final_save = [e for e in arm_events if e["event"] == "checkpoint_saved"][-1]
        assert sha256(checkpoint_path) == final_save["checkpoint_sha256"]
        for name, expected in state["artifact_hashes"].items():
            assert sha256(directory / arm / "workspace" / name) == expected
        assert state["stage"] == "approved" and state["approved"] is True
        assert result["approved"] is True and result["final_review"] == state["final_review"]
        checks[arm] = dict(agent_calls=len(inputs), events=len(arm_events),
            token_usage=metrics["token_usage"],
            cached_input_tokens=sum(e["sdk_usage"]["input_tokens_details"]["cached_tokens"] for e in outputs.values()),
            reasoning_tokens=sum(e["sdk_usage"]["output_tokens_details"]["reasoning_tokens"] for e in outputs.values()),
            checkpoint_loads=counts["checkpoint_loaded"], final_artifact_count=len(state["artifact_hashes"]))
    for field in ("wall_time_s", "agent_runs"):
        assert summary[f"B_minus_A_{field}"] == summary["arms"]["B"]["metrics"][field] - summary["arms"]["A"]["metrics"][field]
    assert summary["B_minus_A_total_tokens"] == checks["B"]["token_usage"]["total_tokens"] - checks["A"]["token_usage"]["total_tokens"]
    report = dict(passed=True, experiment_id=summary["experiment_id"], event_count=len(events), arms=checks,
        summary_sha256=sha256(directory / "summary.json"), events_sha256=sha256(directory / "events.jsonl"),
        verifier_sha256=sha256(Path(__file__)))
    (directory / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1]).resolve()), indent=2))
