"""Fallback / failure-path tests: LLM timeout, tool failure, invalid agent output."""
import asyncio

import pytest

from app.agents.account_agent.agent import AccountAgent
from app.agents.intent_classifier.classifier import IntentClassifierAgent
from app.agents.tools.banking_tools import BalanceInquiryInput, tool_get_balance
from app.clients.llm_client import LLMClient, MockLLMClient
from app.core.exceptions import AgentTimeoutError, LLMProviderError, ToolExecutionError
from app.schemas.chat import AgentContext, IntentType


class _HangingLLM(LLMClient):
    async def complete(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.2) -> str:
        await asyncio.sleep(60)
        return ""


class _FailingBankingClient:
    async def get_balance(self, customer_id: str) -> dict:
        raise RuntimeError("core banking unavailable")


@pytest.mark.asyncio
async def test_intent_classifier_times_out(monkeypatch):
    monkeypatch.setattr("app.agents.intent_classifier.classifier._CLASSIFIER_TIMEOUT_SECONDS", 0.01)
    classifier = IntentClassifierAgent(_HangingLLM())
    with pytest.raises(AgentTimeoutError):
        await classifier.classify("What is my balance?")


@pytest.mark.asyncio
async def test_invalid_llm_output_falls_back_to_heuristics():
    """MockLLMClient returns non-JSON, exercising the invalid-agent-output fallback."""
    classifier = IntentClassifierAgent(MockLLMClient())
    assert await classifier.classify("check my balance") == IntentType.BALANCE_INQUIRY


@pytest.mark.asyncio
async def test_tool_failure_is_wrapped_in_tool_execution_error():
    with pytest.raises(ToolExecutionError):
        await tool_get_balance(_FailingBankingClient(), BalanceInquiryInput(customer_id="cust_1"))


@pytest.mark.asyncio
async def test_account_agent_propagates_tool_failure():
    agent = AccountAgent(_FailingBankingClient())
    context = AgentContext(session_id="s1", customer_id="cust_1", request_id="r1", message="balance")
    with pytest.raises(ToolExecutionError):
        await agent.handle_balance_inquiry(context)


@pytest.mark.asyncio
async def test_complete_json_raises_on_invalid_json():
    class _BadJSONLLM(LLMClient):
        async def complete(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.2) -> str:
            return "not json"

    with pytest.raises(LLMProviderError):
        await _BadJSONLLM().complete_json("sys", "user")
