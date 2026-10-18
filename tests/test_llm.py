import asyncio
from decimal import Decimal
from types import SimpleNamespace

import pytest

from faultline.environment import ToolFailure
from faultline.llm import Budget, BudgetExceeded, Usage, run_llm


async def test_budget_reservations_are_atomic_and_fail_closed():
    budget = Budget(1)
    outcomes = await asyncio.gather(
        *(budget.reserve(Decimal("0.60")) for _ in range(6)), return_exceptions=True
    )
    assert sum(isinstance(o, BudgetExceeded) for o in outcomes) == 5
    assert budget.committed == Decimal("0.60")
    await budget.settle(Decimal("0.60"), Decimal("0.10"))
    await budget.reserve(Decimal("0.60"))
    assert budget.committed == Decimal("0.70")


@pytest.mark.parametrize("value", [0, -1, 5.01])
def test_budget_cap(value):
    with pytest.raises(ValueError):
        Budget(value)


class FakeTools:
    def __init__(self):
        self.transcript = []
        self.calls = 0

    async def schemas(self):
        return []

    async def call(self, name, **arguments):
        self.calls += 1
        raise ToolFailure("503 retry")


def response(message):
    return SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20),
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(model_dump=lambda **_: message), finish_reason="stop"
            )
        ],
    )


async def test_tool_errors_return_to_model_and_usage_is_accounted(monkeypatch):
    import litellm

    count = 0

    async def completion(**kwargs):
        nonlocal count
        count += 1
        assert kwargs["temperature"] == 0.7 and kwargs["num_retries"] == 0
        if count == 1:
            return response(
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call1",
                            "type": "function",
                            "function": {
                                "name": "get_ticket",
                                "arguments": '{"ticket_id": "T-1001"}',
                            },
                        }
                    ],
                }
            )
        assert kwargs["messages"][-1]["content"] == "ERROR: 503 retry"
        return response({"role": "assistant", "content": "done"})

    monkeypatch.setattr(litellm, "acompletion", completion)
    usage, budget = Usage(), Budget()
    await run_llm(FakeTools(), "T-1001", 123, budget, usage)
    assert usage.steps == 2 and usage.prompt_tokens == 200
    assert usage.cost_usd == pytest.approx(float(budget.committed))
    assert usage.reserved_usd == pytest.approx(0)


async def test_failed_api_call_keeps_cost_reservation(monkeypatch):
    import litellm

    async def fail(**kwargs):
        raise TimeoutError("request status unknown")

    monkeypatch.setattr(litellm, "acompletion", fail)
    usage, budget = Usage(), Budget()
    with pytest.raises(TimeoutError):
        await run_llm(FakeTools(), "T-1001", 123, budget, usage)
    assert budget.committed > 0 and usage.reserved_usd > 0


async def test_step_limit(monkeypatch):
    import litellm

    async def completion(**kwargs):
        return response(
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call1",
                        "type": "function",
                        "function": {"name": "get_ticket", "arguments": "{}"},
                    }
                ],
            }
        )

    monkeypatch.setattr(litellm, "acompletion", completion)
    usage = Usage()
    await run_llm(FakeTools(), "T-1001", 123, Budget(), usage)
    assert usage.steps == 15 and usage.finish_reason == "step_limit"


async def test_budget_blocks_request_before_provider_call(monkeypatch):
    import litellm

    async def forbidden(**kwargs):
        pytest.fail("Provider called after budget exhaustion")

    monkeypatch.setattr(litellm, "acompletion", forbidden)
    with pytest.raises(BudgetExceeded):
        await run_llm(FakeTools(), "T-1001", 123, Budget(0.000001), Usage())


async def test_real_litellm_openai_adapter_with_local_http_transport(monkeypatch):
    import httpx
    import litellm
    from openai import AsyncOpenAI

    requests = []

    async def respond(request):
        import json

        body = json.loads(request.content)
        requests.append(body)
        assert body["model"] == "gpt-4.1-mini-2025-04-14"
        assert body["temperature"] == 0.7
        return httpx.Response(
            200,
            json={
                "id": "local-test",
                "object": "chat.completion",
                "created": 0,
                "model": body["model"],
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "done"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
            },
        )

    real_completion = litellm.acompletion
    async with AsyncOpenAI(
        api_key="local-test-placeholder",
        base_url="https://example.test/v1",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        max_retries=0,
    ) as provider:

        async def completion(**kwargs):
            return await real_completion(**kwargs, client=provider)

        monkeypatch.setattr(litellm, "acompletion", completion)
        usage = Usage()
        await run_llm(FakeTools(), "T-1001", 123, Budget(), usage)
    assert len(requests) == 1
    assert usage.steps == 1 and usage.completion_tokens == 20
