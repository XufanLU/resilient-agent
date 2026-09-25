"""Live XAS A/B rerun with per-response usage persisted before tool execution.

RUN_REAL_AGENT_AB_TEST=1 LIVE_AB_ALL_PAIRS=1 python -m pytest -q -s \
    --import-mode=importlib post_submission_2/test_live_agent_ab.py
"""
from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
import traceback
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[1]
AB_DIR = ROOT / "ab_test"
OUTPUT = Path(__file__).resolve().parent
# The vendored scientific workflow uses these top-level imports internally.
if str(AB_DIR) not in sys.path:
    sys.path.insert(0, str(AB_DIR))
from ab_test import test_live_agent_ab as original
from ab_test.usage_tracking import extract_model_token_usage, normalize_token_usage

KEYS = ("input_tokens", "output_tokens", "total_tokens", "requests")


def add(usages):
    usages = list(usages)
    return {key: sum(u[key] for u in usages) for key in KEYS}


def json_value(value):
    """Serialize SDK payloads without relying on unresolved Pydantic serializers."""
    from pydantic import BaseModel
    if isinstance(value, BaseModel):
        return {key: json_value(item) for key, item in value}
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Unsupported event value type: {type(value).__name__}")


class Journal:
    def __init__(self, path):
        self.path = path
        self.sequence = 0
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=False)

    def log(self, event, **fields):
        row = json_value(dict(event=event, sequence=self.sequence + 1,
            timestamp_utc=datetime.now(timezone.utc).isoformat(), **fields))
        line = json.dumps(row, sort_keys=True)
        with self.path.open("a") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.sequence += 1


def make_hooks(journal, arm, phase):
    from agents import RunHooks

    class UsageHooks(RunHooks):
        def __init__(self):
            self.usages = []
            self.tool_calls = Counter()
            self.call_id = None

        async def on_llm_start(self, context, agent, system_prompt, input_items):
            self.call_id = uuid4().hex
            journal.log("model_input", arm=arm, phase=phase, call_id=self.call_id,
                        system_prompt=system_prompt, input_items=input_items)

        async def on_llm_end(self, context, agent, response):
            usage = normalize_token_usage(response.usage)
            if usage["total_tokens"] <= 0:
                raise ValueError("Missing measured response usage")
            journal.log("model_response", arm=arm, phase=phase, call_id=self.call_id,
                        response_id=response.response_id, token_usage=usage,
                        sdk_usage=response.usage, output=response.output)
            self.usages.append(usage)
            assert add(self.usages) == normalize_token_usage(context.usage)

        async def on_tool_start(self, context, agent, tool):
            self.tool_calls[tool.name] += 1
            journal.log("tool_started", arm=arm, phase=phase, tool=tool.name)

        async def on_tool_end(self, context, agent, tool, result):
            journal.log("tool_completed", arm=arm, phase=phase, tool=tool.name, result=result)

    return UsageHooks()


async def run_measured_arm(arm, journal, invoke, clear_cache, snapshot):
    started = time.perf_counter()
    pre = make_hooks(journal, arm, "pre_interruption")
    journal.log("arm_started", arm=arm)
    try:
        await invoke(pre)
    except original.InjectedLiveInterruption:
        assert pre.usages, "Interruption must occur after a recorded model response"
        journal.log("interruption_caught", arm=arm, token_usage=add(pre.usages))
    else:
        raise AssertionError("Expected injected interruption")
    snapshot("interrupted")
    boundary = time.perf_counter()
    if arm == "A":
        clear_cache()
        journal.log("fit_cache_cleared", arm=arm)
    else:
        journal.log("fit_cache_retained", arm=arm)
    recovery = make_hooks(journal, arm, "recovery")
    result = await invoke(recovery)
    assert add(recovery.usages) == extract_model_token_usage(result)
    elapsed = time.perf_counter() - started
    snapshot("completed")
    tool_counts = pre.tool_calls + recovery.tool_calls
    metrics = dict(wall_time_s=elapsed, pre_interruption_wall_time_s=boundary - started,
        recovery_wall_time_s=elapsed - (boundary - started),
        pre_interruption_token_usage=add(pre.usages), recovery_token_usage=add(recovery.usages),
        token_usage=add(pre.usages + recovery.usages),
        tool_calls=dict(total=sum(tool_counts.values()), by_name=dict(tool_counts)),
        final_output=str(result.final_output))
    journal.log("arm_completed", arm=arm, metrics=metrics)
    return metrics


def verify_summary(summary, events_path):
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
    for arm in ("A", "B"):
        m = summary["arms"][arm]
        responses = [e for e in events if e["event"] == "model_response" and e["arm"] == arm]
        assert len({e["call_id"] for e in responses}) == len(responses)
        assert add(e["token_usage"] for e in responses) == m["token_usage"]
        for phase, key in (("pre_interruption", "pre_interruption_token_usage"), ("recovery", "recovery_token_usage")):
            usage = add([e["token_usage"] for e in responses if e["phase"] == phase])
            assert usage == m[key] and usage["total_tokens"] > 0
        assert add([m["pre_interruption_token_usage"], m["recovery_token_usage"]]) == m["token_usage"]
        assert sum(e["event"] == "interruption_caught" and e.get("arm") == arm for e in events) == 1
    return dict(passed=True, events=len(events),
                events_sha256=hashlib.sha256(events_path.read_bytes()).hexdigest())


def validate_completed_checkpoints(checkpoint_dir):
    caches = list(checkpoint_dir.glob("fit_cache_*.json"))
    assert caches, "No fitting checkpoint was saved"
    for path in caches:
        state = json.loads(path.read_text())
        assert all(state.get(key) for key in ("fit_completed", "results_extracted", "visualization_complete")), \
            "Scientific workflow did not complete; model returned after a tool error"
        assert state.get("fitted_parameters") and state.get("path_parameters"), "Missing fitted results"


@pytest.mark.parametrize("pair_id", original._live_pair_ids())
def test_live_first_shell_agent_ab_real_time_and_tokens(pair_id, monkeypatch):
    pair, material_id, xas_path = original._require_live_ab_env(pair_id)
    from dotenv import dotenv_values
    config = {**os.environ, **{k: v for k, v in dotenv_values(ROOT / ".env").items() if v is not None}}
    model = config.get("AB_TEST_MODEL") or config.get("OPENAI_MODEL")
    assert model and config.get("OPENAI_API_KEY"), "Explicit model and API key required"
    monkeypatch.setenv("AB_TEST_MODEL", model)
    results_name = os.getenv("XAS_LIVE_RESULTS_FILENAME", "live_ab_results.jsonl")
    assert Path(results_name).name == results_name and results_name.endswith(".jsonl"), \
        "XAS_LIVE_RESULTS_FILENAME must be a .jsonl filename beneath post_submission_2"
    destination = OUTPUT / results_name
    if destination.exists():
        previous = [json.loads(line) for line in destination.read_text().splitlines() if line.strip()]
        if any(row["pair"]["id"] == pair_id for row in previous):
            pytest.skip(f"Pair already completed in {destination}")

    from agents import Runner, RunConfig, set_default_openai_client, set_tracing_disabled
    from openai import AsyncOpenAI
    from first_shell_agent import create_first_shell_agent
    import data_paths
    from function_calling import artifacts, feff, fit

    run_id = f"{pair_id}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    directory = OUTPUT / "xas_live_runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    journal = Journal(directory / "events.jsonl")
    checkpoint_dir = directory / "working_checkpoints"
    checkpoint_dir.mkdir()
    # Isolate the rerun from historical scientific artifacts. Within-pair A/B
    # sharing of processed artifacts is retained and explicitly recorded.
    monkeypatch.setattr(data_paths, "AB_TEST_ROOT", directory / "scientific_workspace")
    monkeypatch.setattr(fit, "checkpoints_dir", lambda *a, **kw: checkpoint_dir)
    monkeypatch.setattr(feff, "online_cif_data_dir", lambda *a, **kw: AB_DIR / "fixtures")
    original_fit, original_load = fit.execute_first_shell_fit, artifacts.load_fit_group
    state = dict(armed=True, arm="A")
    counts = dict(raw_xas_imports=0, processed_payload_loads=0)

    def fit_then_interrupt(*args, **kwargs):
        result = original_fit(*args, **kwargs)
        if state["armed"]:
            state["armed"] = False
            journal.log("interruption_raised", arm=state["arm"], boundary="after fitting, before checkpoint update")
            raise original.InjectedLiveInterruption("Injected after fitting")
        return result

    def counted_load(*, xas_path=None, xas_ref=None):
        processed = xas_ref or (xas_path and artifacts.load_processed_payload(xas_path) is not None)
        counts["processed_payload_loads" if processed else "raw_xas_imports"] += 1
        return original_load(xas_path=xas_path, xas_ref=xas_ref)

    monkeypatch.setattr(fit, "execute_first_shell_fit", fit_then_interrupt)
    monkeypatch.setattr(artifacts, "load_fit_group", counted_load)
    metadata = dict(protocol="xas_live_full_usage_v1", requested_model=model, arm_order=["A", "B"],
        python=platform.python_version(), packages={p: version(p) for p in ("openai", "openai-agents", "xraylarch", "numpy", "scipy", "pydantic")},
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        original_test_sha256=hashlib.sha256(Path(original.__file__).read_bytes()).hexdigest(),
        xas_sha256=hashlib.sha256(Path(xas_path).read_bytes()).hexdigest(),
        cache_policy="fresh scientific workspace per pair; processed/FEFF artifacts shared A then B within pair, as in original comparison",
        token_scope="all recorded model responses before interruption plus recovery; local fitting itself consumes no model tokens",
        timing_scope="both invocations, cache clearing, synchronous usage logging, interrupted checkpoint snapshot; excludes final snapshot",
        automatic_request_retries=0, tracing_disabled=True)
    (directory / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")

    def snapshot(stage):
        target = directory / state["arm"] / stage
        target.mkdir(parents=True)
        hashes = {}
        for path in checkpoint_dir.glob("*.json"):
            shutil.copy2(path, target / path.name)
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if not hashes:
            raise AssertionError("No fitting checkpoint was saved")
        journal.log("checkpoint_snapshot", arm=state["arm"], stage=stage, hashes=hashes)
        if stage == "completed":
            validate_completed_checkpoints(checkpoint_dir)

    async def execute():
        arms = {}
        async with AsyncOpenAI(api_key=config["OPENAI_API_KEY"], base_url=config.get("OPENAI_BASE_URL"), timeout=120, max_retries=0) as client:
            set_default_openai_client(client, use_for_tracing=False)
            set_tracing_disabled(True)

            async def invoke(hooks):
                agent = await create_first_shell_agent(material_id=material_id, xas_path=xas_path)
                prompt = os.getenv("LIVE_AB_PROMPT", "Run a first-shell EXAFS fit using the current material and XAS spectrum. Use the provided runtime context and return a concise fitting summary.")
                return await Runner.run(agent, prompt, hooks=hooks, run_config=RunConfig(tracing_disabled=True))

            for arm in ("A", "B"):
                print(f"{pair_id}: arm {arm}", flush=True)
                state.update(arm=arm, armed=True)
                counts.update(raw_xas_imports=0, processed_payload_loads=0)
                original._clear_fit_cache(checkpoint_dir)
                arms[arm] = await run_measured_arm(arm, journal, invoke, lambda: original._clear_fit_cache(checkpoint_dir), snapshot)
                arms[arm].update(data_loads=dict(counts), behavior="baseline_restart_from_zero" if arm == "A" else "checkpoint_resume")
                (directory / f"arm_{arm}.json").write_text(json.dumps(arms[arm], indent=2) + "\n")
        return arms

    try:
        arms = asyncio.run(execute())
        summary = dict(schema_version=2, experiment_id=run_id, pair=original._pair_log_context(pair, material_id, xas_path),
            arms=arms, configuration=metadata, result_directory=str(directory), result_log_path=str(destination),
            B_minus_A_wall_time_s=arms["B"]["wall_time_s"] - arms["A"]["wall_time_s"],
            B_minus_A_total_tokens=arms["B"]["token_usage"]["total_tokens"] - arms["A"]["token_usage"]["total_tokens"],
            B_minus_A_raw_xas_imports=arms["B"]["data_loads"]["raw_xas_imports"] - arms["A"]["data_loads"]["raw_xas_imports"])
        validation = verify_summary(summary, journal.path)
        journal.log("pair_completed", pair_id=pair_id)
        validation = verify_summary(summary, journal.path)
        (directory / "verification.json").write_text(json.dumps(validation, indent=2) + "\n")
        (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        with destination.open("a") as handle:
            handle.write(json.dumps(summary, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        print(f"{pair_id}: verified; A={arms['A']['token_usage']['total_tokens']} B={arms['B']['token_usage']['total_tokens']} tokens", flush=True)
    except BaseException as exc:
        failure = dict(error_type=type(exc).__name__, status_code=getattr(exc, "status_code", None),
            stack=[dict(file=f.filename, line=f.lineno, function=f.name) for f in traceback.extract_tb(exc.__traceback__)])
        if isinstance(exc, (TypeError, AssertionError)):
            failure["diagnostic"] = str(exc).replace(config["OPENAI_API_KEY"], "[REDACTED]")
        journal.log("pair_failed", **failure)
        (directory / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
        raise AssertionError(f"Live pair failed: {type(exc).__name__}; inspect {directory}") from None
