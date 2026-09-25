"""Offline checks: interrupted usage survives and is counted exactly once."""
import asyncio
import json
from types import SimpleNamespace

import pytest
from agents import Agent, Runner, RunConfig, function_tool
from agents.items import ModelResponse
from agents.models.interface import Model
from agents.usage import Usage
from openai.types.responses import ResponseFunctionToolCall

from .test_live_agent_ab import Journal, add, make_hooks, original, run_measured_arm, verify_summary, validate_completed_checkpoints


@pytest.mark.parametrize("arm", ["A", "B"])
def test_full_usage_survives_interruption(tmp_path, arm):
    journal = Journal(tmp_path / "events.jsonl")
    attempts, cleared, snapshots = [], [], []

    async def invoke(hooks):
        attempts.append(hooks)
        context = SimpleNamespace(usage=Usage())
        # Two responses before interruption; one during recovery.
        for index in range(2 if len(attempts) == 1 else 1):
            usage = Usage(requests=1, input_tokens=7, output_tokens=3, total_tokens=10)
            context.usage.add(usage)
            await hooks.on_llm_start(context, None, "instructions", [])
            await hooks.on_llm_end(context, None, SimpleNamespace(usage=usage, response_id=f"response-{len(attempts)}-{index}", output=[]))
        if len(attempts) == 1:
            raise original.InjectedLiveInterruption()
        return SimpleNamespace(context_wrapper=context, final_output="completed")

    result = asyncio.run(run_measured_arm(arm, journal, invoke, lambda: cleared.append(True), snapshots.append))
    assert result["pre_interruption_token_usage"]["total_tokens"] == 20
    assert result["recovery_token_usage"]["total_tokens"] == 10
    assert result["token_usage"] == dict(input_tokens=21, output_tokens=9, total_tokens=30, requests=3)
    assert cleared == ([True] if arm == "A" else [])
    assert snapshots == ["interrupted", "completed"]
    events = [json.loads(line) for line in journal.path.read_text().splitlines()]
    assert add(e["token_usage"] for e in events if e["event"] == "model_response") == result["token_usage"]


def test_real_sdk_calls_usage_hook_before_interrupting_tool(tmp_path):
    journal = Journal(tmp_path / "events.jsonl")
    hooks = make_hooks(journal, "A", "pre_interruption")

    class FakeModel(Model):
        async def get_response(self, *args, **kwargs):
            return ModelResponse(output=[ResponseFunctionToolCall(type="function_call", name="interrupt", arguments="{}", call_id="tool-1")],
                usage=Usage(requests=1, input_tokens=12, output_tokens=4, total_tokens=16), response_id="offline-response")

        async def stream_response(self, *args, **kwargs):
            raise NotImplementedError
            yield

    @function_tool
    def interrupt() -> str:
        """Interrupt execution after the model has requested this tool."""
        assert hooks.usages[0]["total_tokens"] == 16
        assert '"model_response"' in journal.path.read_text()
        raise original.InjectedLiveInterruption()

    async def run():
        with pytest.raises(original.InjectedLiveInterruption):
            await Runner.run(Agent(name="offline", model=FakeModel(), tools=[interrupt]), "Run the tool", hooks=hooks,
                             run_config=RunConfig(tracing_disabled=True))
    asyncio.run(run())
    assert add(hooks.usages)["total_tokens"] == 16


def test_missing_usage_is_rejected(tmp_path):
    hooks = make_hooks(Journal(tmp_path / "events.jsonl"), "A", "pre_interruption")
    with pytest.raises(ValueError, match="Missing measured"):
        asyncio.run(hooks.on_llm_end(SimpleNamespace(usage=Usage()), None,
            SimpleNamespace(usage=Usage(), response_id="missing", output=[])))


def test_real_http_client_response_is_logged_offline(tmp_path):
    import httpx
    from openai import AsyncOpenAI
    from agents.models.openai_responses import OpenAIResponsesModel

    async def transport(request):
        return httpx.Response(200, json={"id": "resp_offline", "object": "response", "created_at": 1,
            "status": "completed", "model": "gpt-5.4", "output": [{"type": "message", "id": "msg_offline",
                "role": "assistant", "status": "completed", "content": [{"type": "output_text",
                    "text": "Offline response", "annotations": []}]}],
            "usage": {"input_tokens": 11, "output_tokens": 4, "total_tokens": 15,
                "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 0}},
            "parallel_tool_calls": True, "tools": [], "tool_choice": "auto"})

    async def run():
        async with AsyncOpenAI(api_key="offline-test-only", max_retries=0,
                http_client=httpx.AsyncClient(transport=httpx.MockTransport(transport))) as client:
            journal = Journal(tmp_path / "events.jsonl")
            hooks = make_hooks(journal, "A", "pre_interruption")
            agent = Agent(name="offline", model=OpenAIResponsesModel("gpt-5.4", client))
            result = await Runner.run(agent, "offline", hooks=hooks, run_config=RunConfig(tracing_disabled=True))
            assert result.final_output == "Offline response"
            response = json.loads(journal.path.read_text().splitlines()[-1])
            assert response["sdk_usage"]["input_tokens_details"]["cached_tokens"] == 0
            assert add(hooks.usages)["total_tokens"] == 15
    asyncio.run(run())


@pytest.mark.parametrize("complete", [False, True])
def test_tool_error_cannot_be_reported_as_completed_fit(tmp_path, complete):
    state = dict(fit_completed=True, results_extracted=True,
                 visualization_complete=complete, fitted_parameters={"amp": .8}, path_parameters=[{"path": 1}])
    (tmp_path / "fit_cache_test.json").write_text(json.dumps(state))
    if complete:
        validate_completed_checkpoints(tmp_path)
    else:
        with pytest.raises(AssertionError, match="Scientific workflow did not complete"):
            validate_completed_checkpoints(tmp_path)
